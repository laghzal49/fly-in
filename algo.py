"""Pathfinding for drones with zone and link capacity rules."""

from __future__ import annotations

import heapq

from graph import GraphNetwork
from parser import Hub
from reservation import ReservationTable

PathStep = tuple[str, int]
HeapItem = tuple[int, str, int, list[PathStep]]

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
        self.zone_use: dict[str, int] = {}
        self.link_use: dict[str, int] = {}

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
        """Return useful neighbors, with priority zones first."""
        result: list[Hub] = []
        for hub in self.graph.get_neighbor(zone):
            if hub.name in self.can_reach:
                result.append(hub)

        result.sort(key=lambda hub: ZONE_PRIO.get(hub.zone, 1))
        return result

    def _link_name(self, src: str, dst: str) -> str:
        """Return the internal key for a link."""
        return f"{min(src, dst)}_{max(src, dst)}"

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

    def _max_turn(self) -> int:
        """Keep waiting bounded."""
        last_turn = 0
        for _, turn in self.table.table:
            last_turn = max(last_turn, turn)
        return last_turn + len(self.graph.hubs) * 4 + 10

    def _move_steps(self, src: str, dst: str, turn: int) -> list[PathStep]:
        """Build path steps for one move."""
        if self.graph.hubs[dst].zone == "restricted":
            return [(f"{src}-{dst}", turn + 1), (dst, turn + 2)]
        return [(dst, turn + 1)]

    def _congestion(self, src: str, dst: str) -> int:
        """Prefer paths used less by previous drones."""
        link = self._link_name(src, dst)
        return self.zone_use.get(dst, 0) + self.link_use.get(link, 0)

    def _path_zones(self, path: list[PathStep]) -> set[str]:
        """Return real zones already used by a path."""
        zones: set[str] = set()
        for step, _ in path:
            if "-" not in step:
                zones.add(step)
        return zones

    def _can_move(
        self,
        src: str,
        dst: str,
        turn: int,
        start: str,
        end: str,
    ) -> bool:
        """Check if a move respects zone and link capacity."""
        if self.graph.hubs[dst].zone == "restricted":
            link_ok = self._link_free(src, dst, turn + 1) and self._link_free(
                src, dst, turn + 2
            )
            return link_ok and self._zone_free(dst, turn + 2, start, end)

        return self._link_free(src, dst, turn + 1) and self._zone_free(
            dst, turn + 1, start, end
        )

    def find_path(self, start: str, end: str) -> list[PathStep]:
        """Find the shortest available path for one drone."""
        if not self.can_reach:
            self._mark_reachable(end)
        if start not in self.can_reach:
            return []

        max_turn = self._max_turn()
        heap: list[HeapItem] = [(0, start, 0, [(start, 0)])]
        best_score: dict[tuple[str, int], int] = {}

        while heap:
            score, zone, turn, path = heapq.heappop(heap)

            if zone == end:
                return path

            state = (zone, turn)
            if state in best_score and best_score[state] <= score:
                continue
            best_score[state] = score

            visited = self._path_zones(path)
            for neighbor in self._neighbors(zone):
                dst = neighbor.name
                if dst in visited and dst != end:
                    continue
                if not self._can_move(zone, dst, turn, start, end):
                    continue

                extra = self._move_steps(zone, dst, turn)
                next_turn = extra[-1][1]
                next_score = next_turn * 100 + self._congestion(zone, dst)
                heapq.heappush(
                    heap,
                    (next_score, dst, next_turn, path + extra),
                )

            if turn + 1 <= max_turn:
                self._push_wait(heap, score, zone, turn, path, start, end)

        return []

    def _push_wait(
        self,
        heap: list[HeapItem],
        score: int,
        zone: str,
        turn: int,
        path: list[PathStep],
        start: str,
        end: str,
    ) -> None:
        """Push a one-turn wait if the zone has capacity."""
        if not self._zone_free(zone, turn + 1, start, end):
            return

        heapq.heappush(
            heap,
            (score + 100, zone, turn + 1, path + [(zone, turn + 1)]),
        )

    def _reserve(self, path: list[PathStep]) -> None:
        """Reserve all zones and links used by a path."""
        for i, (step, turn) in enumerate(path):
            if "-" in step:
                self._reserve_restricted_link(step, turn)
                continue

            self._reserve_zone_step(path, i, step, turn)

    def _reserve_restricted_link(self, step: str, turn: int) -> None:
        """Reserve a restricted connection for two turns."""
        src, dst = step.split("-", 1)
        link = self._link_name(src, dst)

        self.table.reserve_link(src, dst, turn)
        self.table.reserve_link(src, dst, turn + 1)
        self.link_use[link] = self.link_use.get(link, 0) + 1

    def _reserve_zone_step(
        self,
        path: list[PathStep],
        index: int,
        zone: str,
        turn: int,
    ) -> None:
        """Reserve a zone step and its normal incoming link."""
        self.table.reserve_zone(zone, turn)
        self.zone_use[zone] = self.zone_use.get(zone, 0) + 1

        if index == 0:
            return

        prev_zone, _ = path[index - 1]
        if "-" in prev_zone or prev_zone == zone:
            return

        link = self._link_name(prev_zone, zone)
        self.table.reserve_link(prev_zone, zone, turn)
        self.link_use[link] = self.link_use.get(link, 0) + 1

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
