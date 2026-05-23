import heapq
from drone import Drone, MoveStep
from graph import GraphNetwork
from parser import Hub

ZONE_PRIO: dict[str, int] = {
    "priority": 0,
    "normal": 1,
    "restricted": 2,
}


class PathFinder:
    """Find and reserve one valid path per drone."""

    def __init__(self, graph: GraphNetwork) -> None:
        """Store graph reference."""
        self.graph: GraphNetwork = graph
        self.can_reach: set[str] = set()
        self._max_turn: int = 0

    def _mark_reachable(self, end: str) -> None:
        """Mark all hubs that can reach the end."""
        self.can_reach.clear()
        stack = [end]
        while stack:
            zone = stack.pop()
            if zone in self.can_reach:
                continue
            self.can_reach.add(zone)
            for hub in self.graph.get_neighbor(zone):
                stack.append(hub.name)

    def _neighbors(self, zone: str) -> list[Hub]:
        """Reachable neighbors, sorted by priority."""
        reachable = [
            h for h in self.graph.get_neighbor(zone)
            if h.name in self.can_reach
        ]
        return sorted(
            reachable,
            key=lambda h: ZONE_PRIO.get(h.zone, 1),
        )

    def _zone_free(
        self, zone: str, turn: int,
        start: str, end: str,
    ) -> bool:
        """True if a zone has room at a turn."""
        if zone == start or zone == end:
            return True
        return self.graph.hubs[zone].is_available(turn)

    def _link_free(
        self, src: str, dst: str, turn: int,
    ) -> bool:
        """True if a link has room at a turn."""
        conn = self.graph.get_connection(src, dst)
        assert conn is not None
        return conn.is_available(turn)

    def _can_move(
        self, src: str, dst: str, turn: int,
        start: str, end: str,
    ) -> bool:
        """True if move respects all capacity."""
        if not self._link_free(src, dst, turn + 1):
            return False

        hub = self.graph.hubs[dst]
        if hub.zone == "restricted":
            return (
                self._link_free(src, dst, turn + 2)
                and self._zone_free(
                    dst, turn + 2, start, end,
                )
            )
        return self._zone_free(
            dst, turn + 1, start, end,
        )

    def _move_steps(
        self, src: str, dst: str, turn: int,
    ) -> list[MoveStep]:
        """Build path steps for one move."""
        if self.graph.hubs[dst].zone == "restricted":
            return [
                MoveStep.on_link(src, dst, turn + 1),
                MoveStep.at_zone(dst, turn + 2),
            ]
        return [
            MoveStep.at_zone(
                dst, turn + 1, via=(src, dst),
            ),
        ]

    def find_path(
        self, start: str, end: str,
    ) -> list[MoveStep]:
        """Find shortest path for one drone."""
        if not self.can_reach:
            self._mark_reachable(end)
        if start not in self.can_reach:
            return []

        limit = self._max_turn + len(self.graph.hubs) * 4
        initial = MoveStep.at_zone(start, 0)
        start_prio = ZONE_PRIO.get(
            self.graph.hubs[start].zone, 1,
        )
        heap = [(0, 0, start_prio, start, [initial])]
        seen: set[tuple[str, int]] = set()

        while heap:
            turn, cost, _, zone, path = heapq.heappop(
                heap,
            )
            if zone == end:
                return path
            if (zone, turn) in seen:
                continue
            seen.add((zone, turn))

            for neighbor in self._neighbors(zone):
                dst = neighbor.name
                if not self._can_move(
                    zone, dst, turn, start, end,
                ):
                    continue
                steps = self._move_steps(
                    zone, dst, turn,
                )
                arrival = steps[-1].turn
                if arrival > limit:
                    continue
                prio = ZONE_PRIO.get(
                    neighbor.zone, 1,
                )
                heapq.heappush(heap, (
                    arrival, cost + prio, prio,
                    dst, path + steps,
                ))
            wait = turn + 1
            if wait <= limit and self._zone_free(
                zone, wait, start, end,
            ):
                prio = ZONE_PRIO.get(
                    self.graph.hubs[zone].zone, 1,
                )
                heapq.heappush(heap, (
                    wait, cost + prio, prio, zone,
                    path + [
                        MoveStep.at_zone(zone, wait),
                    ],
                ))

        return []

    def _reserve(
        self, path: list[MoveStep],
    ) -> None:
        """Reserve all zones and links in a path."""
        for step in path:
            if step.is_link:
                assert step.src and step.dst
                conn = self.graph.get_connection(
                    step.src, step.dst,
                )
                if conn:
                    conn.reserve(step.turn)
                    conn.reserve(step.turn + 1)
            else:
                assert step.zone is not None
                self.graph.hubs[step.zone].reserve(
                    step.turn,
                )
                if step.via:
                    conn = self.graph.get_connection(
                        *step.via,
                    )
                    if conn:
                        conn.reserve(step.turn)

        if path:
            last = path[-1].turn
            if last > self._max_turn:
                self._max_turn = last

    def assign_all_paths(
        self, start: str, end: str, nb_drones: int,
    ) -> list[Drone]:
        """Find and reserve a path for every drone."""
        self._mark_reachable(end)
        drones: list[Drone] = []

        for drone_id in range(1, nb_drones + 1):
            drone = Drone(drone_id, start, end)
            path = self.find_path(start, end)
            if not path:
                raise ValueError(
                    f"No path for drone {drone.name}",
                )
            drone.path = path
            self._reserve(path)
            drones.append(drone)

        return drones
