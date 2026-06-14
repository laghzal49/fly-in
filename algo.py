"""Pathfinding for drones with capacity rules."""

import heapq
from typing import Dict, List, Set, Tuple

from graph import GraphNetwork
from parser import Hub
from zone import ReservationTable

# lower value = try this zone type first
ZONE_PRIO: Dict[str, int] = {
    "priority": 0,
    "normal": 1,
    "restricted": 2,
}

PathStep = Tuple[str, int]
HeapItem = Tuple[
    float, int, str, int, List[PathStep], frozenset[str]
]


class PathFinder:
    """Find paths for each drone using a space-time search."""

    def __init__(
        self, graph: GraphNetwork, table: ReservationTable
    ) -> None:
        """Store graph and reservation table."""
        self.graph = graph
        self.table = table
        self.heap_id = 0
        self.can_reach: Set[str] = set()

    def _next_heap_id(self) -> int:
        """Return a new id so heap items stay stable."""
        self.heap_id += 1
        return self.heap_id

    def _mark_reachable(self, end: str) -> None:
        """Mark all hubs that can reach the goal (reverse BFS)."""
        self.can_reach.clear()
        todo = [end]
        while todo:
            cur = todo.pop()
            if cur in self.can_reach:
                continue
            self.can_reach.add(cur)
            for n in self.graph.get_neighbor(cur):
                if n.name not in self.can_reach:
                    todo.append(n.name)

    def _sorted_neighbors(self, zone: str) -> List[Hub]:
        """Return neighbors that can still reach the goal."""
        nb: List[Hub] = []
        for n in self.graph.get_neighbor(zone):
            if n.name in self.can_reach:
                nb.append(n)
        nb.sort(key=lambda h: ZONE_PRIO.get(h.zone, 1))
        return nb

    def _zone_free(
        self, name: str, turn: int, cap: int, goal: str
    ) -> bool:
        """Check if a zone has room at the arrival turn."""
        if name == goal:
            return True

        hub = self.graph.hubs.get(name)
        if hub and hub.zone == "restricted":
            ok_prev = self.table.is_zone_available(
                name, turn - 1, cap
            )
            ok_now = self.table.is_zone_available(name, turn, cap)
            return ok_prev and ok_now

        return self.table.is_zone_available(name, turn, cap)

    def _link_free(
        self, src: str, dst: str, t_start: int, t_end: int
    ) -> bool:
        """Check if a link is free during travel."""
        conn = self.graph.get_connection(src, dst)
        cap = conn.max_link_capacity if conn else 1
        t = t_start + 1
        while t <= t_end:
            if not self.table.is_link_available(src, dst, t, cap):
                return False
            t += 1
        return True

    def _max_turn_limit(self) -> int:
        """Compute a safe upper bound for waiting turns."""
        last_turn = 0
        for (_, turn) in self.table.table:
            if turn > last_turn:
                last_turn = turn
        return last_turn + len(self.graph.hubs) * 4 + 10

    def find_path(self, start: str, end: str) -> List[PathStep]:
        """Find one shortest valid path for a single drone."""
        if end not in self.can_reach:
            self._mark_reachable(end)
        if start not in self.can_reach:
            return []

        max_turn = self._max_turn_limit()
        start_path: List[PathStep] = [(start, 0)]
        pq: List[HeapItem] = [
            (
                0.0,
                self._next_heap_id(),
                start,
                0,
                start_path,
                frozenset([start]),
            )
        ]
        seen_states: Set[Tuple[str, int]] = set()

        while pq:
            cost, _, zone, turn, path, visited = heapq.heappop(pq)

            if zone == end:
                return path
            if (zone, turn) in seen_states:
                continue
            seen_states.add((zone, turn))

            for n in self._sorted_neighbors(zone):
                if n.name in visited:
                    continue

                steps = 2 if n.zone == "restricted" else 1
                arrive = turn + steps

                if not self._zone_free(
                    n.name, arrive, n.max_drones, end
                ):
                    continue
                if not self._link_free(zone, n.name, turn, arrive):
                    continue

                if n.zone == "restricted":
                    new_path = path + [
                        (f"{zone}-{n.name}", turn + 1),
                        (n.name, arrive),
                    ]
                else:
                    new_path = path + [(n.name, arrive)]

                item: HeapItem = (
                    cost + steps,
                    self._next_heap_id(),
                    n.name,
                    arrive,
                    new_path,
                    visited | {n.name},
                )
                heapq.heappush(pq, item)

            hub = self.graph.hubs[zone]
            cap = 9999 if zone == start else hub.max_drones
            can_wait = (
                self._sorted_neighbors(zone)
                and turn + 1 <= max_turn
                and self.table.is_zone_available(zone, turn + 1, cap)
            )
            if can_wait:
                wait_path = path + [(zone, turn + 1)]
                wait_item: HeapItem = (
                    cost + 1.0,
                    self._next_heap_id(),
                    zone,
                    turn + 1,
                    wait_path,
                    visited,
                )
                heapq.heappush(pq, wait_item)

        return []

    def _reserve(self, path: List[PathStep]) -> None:
        """Save path usage in the reservation table."""
        i = 0
        while i < len(path):
            zone, turn = path[i]
            if i == 0:
                self.table.reserve_zone(zone, turn)
            elif "-" in zone:
                a, b = zone.split("-")
                self.table.reserve_link(a, b, turn)
                self.table.reserve_zone(b, turn)
                self.table.reserve_zone(b, turn + 1)
            else:
                prev_zone, prev_turn = path[i - 1]
                if "-" not in prev_zone:
                    self.table.reserve_zone(zone, turn)
                    t = prev_turn + 1
                    while t <= turn:
                        self.table.reserve_link(prev_zone, zone, t)
                        t += 1
            i += 1

    def assign_all_paths(
        self, start: str, end: str, nb_drones: int
    ) -> Dict[int, List[PathStep]]:
        """Find and reserve a path for every drone."""
        self._mark_reachable(end)
        all_paths: Dict[int, List[PathStep]] = {}

        for drone in range(1, nb_drones + 1):
            path = self.find_path(start, end)
            if not path:
                raise ValueError(f"No path for drone D{drone}")
            self._reserve(path)
            all_paths[drone] = path

        return all_paths
