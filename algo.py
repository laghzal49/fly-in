from typing import Dict, List, Tuple, Set
import heapq
from zone import ReservationTable
from graph import GraphNetwork
from parser import Hub

ZONE_ORDER: Dict[str, int] = {"priority": 0, "normal": 1, "restricted": 2}


class PathFinder:
    """
    Finds paths for drones through the graph network using A* algorithm,
    considering zone capacities and restricted zone rules.
    """

    def __init__(self, graph: GraphNetwork, table: ReservationTable) -> None:
        """
        Initializes the PathFinder with a graph and a reservation table.
        """
        self.graph = graph
        self.table = table
        self._counter: int = 0
        self._reachable: Set[str] = set()

    def _next(self) -> int:
        """
        Generates a unique counter for heap sorting stability.
        """
        self._counter += 1
        return self._counter

    def _compute_reachable(self, end: str) -> None:
        """
        Pre-computes reachable nodes from the destination using BFS backwards.
        """
        queue = [end]
        while queue:
            node = queue.pop()
            if node in self._reachable:
                continue
            self._reachable.add(node)
            for n in self.graph.get_neighbor(node):
                if n.name not in self._reachable:
                    queue.append(n.name)

    def _neighbors(self, zone: str) -> List[Hub]:
        """
        Returns sorted reachable neighbors of a zone.
        """
        return sorted(
            [n for n in self.graph.get_neighbor(zone)
             if n.name in self._reachable],
            key=lambda n: ZONE_ORDER.get(n.zone, 1),
        )

    def _node_clear(self, target: str, arrival: int,
                    max_drones: int, end: str) -> bool:
        """
        Checks if a target zone is clear for entry at a specific turn.
        """
        if target == end:
            return True
        hub = self.graph.hubs.get(target)
        if hub and hub.zone == "restricted":
            return (
                self.table.is_zone_available(target, arrival - 1, max_drones)
                and self.table.is_zone_available(target, arrival, max_drones)
            )
        return self.table.is_zone_available(target, arrival, max_drones)

    def _link_clear(self, src: str, dst: str,
                    start_turn: int, end_turn: int) -> bool:
        """
        Checks if a link between two zones is clear during the travel duration.
        """
        conn = self.graph.get_connection(src, dst)
        cap = conn.max_link_capacity if conn else 1
        return all(
            self.table.is_link_available(src, dst, t, cap)
            for t in range(start_turn + 1, end_turn + 1)
        )

    def find_path(self, start: str, end: str) -> List[Tuple[str, int]]:
        """
        Finds the shortest path from start to end for a single drone.
        """
        # cost, counter, zone, turn, path, seen
        heap: List[Tuple[float, int, str, int,
                         List[Tuple[str, int]], frozenset[str]]] = [
            (0.0, self._next(), start, 0, [(start, 0)], frozenset([start]))
        ]
        visited: Set[Tuple[str, int]] = set()

        while heap:
            cost, _, zone, turn, path, seen = heapq.heappop(heap)

            if zone == end:
                return path
            if (zone, turn) in visited:
                continue
            visited.add((zone, turn))

            for nb in self._neighbors(zone):
                if nb.name in seen:
                    continue
                duration = 2 if nb.zone == "restricted" else 1
                arrival = turn + duration

                if not self._node_clear(nb.name, arrival, nb.max_drones, end):
                    continue
                if not self._link_clear(zone, nb.name, turn, arrival):
                    continue

                if nb.zone == "restricted":
                    step = path + [(f"{zone}-{nb.name}", turn + 1),
                                   (nb.name, arrival)]
                else:
                    step = path + [(nb.name, arrival)]

                heapq.heappush(heap, (
                    cost + duration, self._next(),
                    nb.name, arrival, step, seen | {nb.name}
                ))
            hub = self.graph.hubs[zone]
            cap = 9999 if zone == start else hub.max_drones
            if self.table.is_zone_available(zone, turn + 1, cap):
                heapq.heappush(heap, (
                    cost + 1.0, self._next(),
                    zone, turn + 1, path + [(zone, turn + 1)], seen
                ))

        return []

    def _reserve(self, path: List[Tuple[str, int]]) -> None:
        """
        Reserves the capacity along the given path in the reservation table.
        """
        for i, (zone, turn) in enumerate(path):
            if i == 0:
                self.table.reserve_zone(zone, turn)
                continue
            if "-" in zone:
                parts = zone.split("-")
                self.table.reserve_link(parts[0], parts[1], turn)
                self.table.reserve_zone(parts[1], turn)
                self.table.reserve_zone(parts[1], turn + 1)
            else:
                self.table.reserve_zone(zone, turn)
                prev_zone, prev_turn = path[i - 1]
                if "-" not in prev_zone:
                    for t in range(prev_turn + 1, turn + 1):
                        self.table.reserve_link(prev_zone, zone, t)

    def assign_all_paths(self, start: str, end: str,
                         drone_num: int) -> Dict[int, List[Tuple[str, int]]]:
        """
        Finds and reserves paths for all drones.
        """
        self._compute_reachable(end)
        paths: Dict[int, List[Tuple[str, int]]] = {}
        for drone_id in range(1, drone_num + 1):
            path = self.find_path(start, end)
            if not path:
                raise ValueError(f"No path for drone D{drone_id}")
            self._reserve(path)
            paths[drone_id] = path
        return paths
