"""Tracks which zones and links are busy at each turn."""

from typing import Dict, Tuple


class ReservationTable:
    """Counts how many drones use a zone or link per turn."""

    def __init__(self) -> None:
        """Create an empty reservation table."""
        self.table: Dict[Tuple[str, int], int] = {}

    def reserve_zone(self, zone_name: str, turn: int) -> None:
        """Mark one drone in a zone for a given turn."""
        key = (zone_name, turn)
        self.table[key] = self.table.get(key, 0) + 1

    def is_zone_available(
        self, zone_name: str, turn: int, max_drones: int
    ) -> bool:
        """Return True if the zone still has free capacity."""
        count = self.table.get((zone_name, turn), 0)
        return count < max_drones

    def reserve_link(self, z1: str, z2: str, turn: int) -> None:
        """Mark one drone on a link for a given turn."""
        link = f"{min(z1, z2)}_{max(z1, z2)}"
        key = (link, turn)
        self.table[key] = self.table.get(key, 0) + 1

    def is_link_available(
        self, z1: str, z2: str, turn: int, max_link_capacity: int
    ) -> bool:
        """Return True if the link still has free capacity."""
        link = f"{min(z1, z2)}_{max(z1, z2)}"
        count = self.table.get((link, turn), 0)
        return count < max_link_capacity
