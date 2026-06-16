from __future__ import annotations

import heapq

from graph import GraphNetwork
from parser import Hub
from reservation import ReservationTable

PathStep = tuple[str, int]
HeapItem = tuple[int, int, str, list[PathStep]]

ZONE_PRIO: dict[str, int] = {
    "priority": 0,
    "normal": 1,
    "restricted": 2,
}


class PathFinder:
    """Find and reserve one valid path per drone."""

    def __init__(self, graph: GraphNetwork, table: ReservationTable) -> None:
        """Store graph and reservation state."""
        self.graph: GraphNetwork = graph
        self.table: ReservationTable = table
        self.can_reach: set[str] = set()

    def _mark_reachable(self, end: str) -> None:
        """Mark all hubs that can reach the end."""
        self.can_reach.clear()
        stack = [end]

        while stack:
            zone = stack.pop()
            if zone in self.can_reach:
                continue

            self.can_reach.add(zone)
            for neighbor in self.graph.get_neighbor(zone):
                stack.append(neighbor.name)

    def _neighbors(self, zone: str) -> list[Hub]:
        """Return reachable neighbors heading toward the end."""
        return [
            hub for hub in self.graph.get_neighbor(zone)
            if hub.name in self.can_reach
        ]

    def _zone_free(
        self,
        zone: str,
        turn: int,
        start: str,
        end: str,
    ) -> bool:
        """Return True if a zone has room at a turn."""
        if zone == start or zone == end:
            return True

        hub = self.graph.hubs[zone]
        return self.table.is_zone_available(zone, turn, hub.max_drones)

    def _link_free(self, src: str, dst: str, turn: int) -> bool:
        """Return True if a link has room at a turn."""
        conn = self.graph.get_connection(src, dst)
        cap = conn.max_link_capacity if conn else 1
        return self.table.is_link_available(src, dst, turn, cap)

    def _move_steps(self, src: str, dst: str, turn: int) -> list[PathStep]:
        """Build path steps for one move."""
        if self.graph.hubs[dst].zone == "restricted":
            return [(f"{src}-{dst}", turn + 1), (dst, turn + 2)]
        return [(dst, turn + 1)]

    def _can_move(
        self,
        src: str,
        dst: str,
        turn: int,
        start: str,
        end: str,
    ) -> bool:
        """Check if a move respects zone and link capacity."""
        if not self._link_free(src, dst, turn + 1):
            return False

        if self.graph.hubs[dst].zone == "restricted":
            if not self._link_free(src, dst, turn + 2):
                return False
            if not self._zone_free(dst, turn + 2, start, end):
                return False
        else:
            if not self._zone_free(dst, turn + 1, start, end):
                return False

        return True

    def find_path(self, start: str, end: str) -> list[PathStep]:
        """Find the shortest path for one drone using Dijkstra's algorithm."""
        if not self.can_reach:
            self._mark_reachable(end)

        if start not in self.can_reach:
            return []

        max_turn = self.table.max_turn
        max_turn += len(self.graph.hubs) * 4
        start_prio = ZONE_PRIO.get(self.graph.hubs[start].zone, 1)
        heap: list[HeapItem] = [(0, start_prio, start, [(start, 0)])]
        seen: set[tuple[str, int]] = set()

        while heap:
            turn, _, zone, path = heapq.heappop(heap)

            if zone == end:
                return path

            state = (zone, turn)
            if state in seen:
                continue
            seen.add(state)

            for neighbor in self._neighbors(zone):
                dst = neighbor.name

                if not self._can_move(zone, dst, turn, start, end):
                    continue

                steps = self._move_steps(zone, dst, turn)
                next_turn = steps[-1][1]
                prio = ZONE_PRIO.get(neighbor.zone, 1)

                heapq.heappush(
                    heap,
                    (next_turn, prio, dst, path + steps),
                )
            if turn + 1 <= max_turn and self._zone_free(
                    zone, turn + 1, start, end):
                prio = ZONE_PRIO.get(self.graph.hubs[zone].zone, 1)
                heapq.heappush(
                    heap,
                    (turn + 1, prio, zone, path + [(zone, turn + 1)]),
                )

        return []

    def _reserve(self, path: list[PathStep]) -> None:
        """Reserve all zones and links used by a path."""
        for i, (step, turn) in enumerate(path):
            if "-" in step:
                src, dst = step.split("-", 1)
                self.table.reserve_link(src, dst, turn)
                self.table.reserve_link(src, dst, turn + 1)
                continue

            self.table.reserve_zone(step, turn)

            if i > 0:
                prev_zone, _ = path[i - 1]
                if "-" not in prev_zone and prev_zone != step:
                    self.table.reserve_link(prev_zone, step, turn)

    def assign_all_paths(
        self,
        start: str,
        end: str,
        nb_drones: int,
    ) -> dict[int, list[PathStep]]:
        """Find every drone path, reserving each path immediately."""
        self._mark_reachable(end)
        paths: dict[int, list[PathStep]] = {}

        for drone in range(1, nb_drones + 1):
            path = self.find_path(start, end)
            if not path:
                raise ValueError(f"No path for drone D{drone}")
            self._reserve(path)
            paths[drone] = path

        return paths
