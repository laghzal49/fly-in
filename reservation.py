"""Reservation table for zone and link capacity."""

from __future__ import annotations


class ReservationTable:
    """Count how many drones use each zone/link at each turn."""

    def __init__(self) -> None:
        self.table: dict[tuple[str, int], int] = {}

    def _add(self, name: str, turn: int) -> None:
        key = (name, turn)
        self.table[key] = self.table.get(key, 0) + 1

    def _count(self, name: str, turn: int) -> int:
        return self.table.get((name, turn), 0)

    def _link_name(self, z1: str, z2: str) -> str:
        return f"{min(z1, z2)}_{max(z1, z2)}"

    def reserve_zone(self, zone: str, turn: int) -> None:
        """Reserve one drone in a zone at a turn."""
        self._add(zone, turn)

    def is_zone_available(self, zone: str, turn: int, capacity: int) -> bool:
        """Return True if a zone still has room."""
        return self._count(zone, turn) < capacity

    def reserve_link(self, z1: str, z2: str, turn: int) -> None:
        """Reserve one drone on a link at a turn."""
        self._add(self._link_name(z1, z2), turn)

    def is_link_available(
        self,
        z1: str,
        z2: str,
        turn: int,
        capacity: int,
    ) -> bool:
        """Return True if a link still has room."""
        return self._count(self._link_name(z1, z2), turn) < capacity

    @property
    def max_turn(self) -> int:
        """Return the highest turn currently reserved, or 0 if empty."""
        if not self.table:
            return 0
        return max(turn for _, turn in self.table.keys())
