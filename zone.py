from typing import List, Tuple, Dict


class Drone:
    """
    Represents a drone in the simulation.
    """

    def __init__(self, drone_id: int, path: List[Tuple[str, int]]) -> None:
        """
        Initializes a drone with an ID and a path.
        """
        self.id: int = drone_id
        self.name: str = f"D{drone_id}"
        self.path: List[Tuple[str, int]] = path
        self.path_index: int = 0

    def is_delivered(self, end_zone: str) -> bool:
        """
        Checks if the drone has reached the destination zone.
        """
        return self.get_current_zone_name() == end_zone

    def get_current_zone_name(self) -> str:
        """
        Returns the name of the current zone the drone is in.
        """
        return self.path[self.path_index][0]

    def get_next_zone_name(self) -> str:
        """
        Returns the name of the next zone in the drone's path.
        """
        if self.path_index + 1 >= len(self.path):
            return self.path[self.path_index][0]
        return self.path[self.path_index + 1][0]


class Zone:
    """
    Represents a zone in the simulation with a maximum drone capacity.
    """

    def __init__(self, name: str, max_drones: int, zone_type: str) -> None:
        """
        Initializes a zone with a name, capacity, and type.
        """
        self.name: str = name
        self.max_drones: int = max_drones
        self.zone_type: str = zone_type
        self.occupants: List[Drone] = []

    def has_capacity(self) -> bool:
        """
        Fluid calculation: room is safe if net balance doesn't blow past max.
        """
        return len(self.occupants) < self.max_drones

    def accept_drone(self, drone: Drone) -> None:
        """
        Adds a drone to the zone's occupants.
        """
        self.occupants.append(drone)

    def release_drone(self, drone: Drone) -> None:
        """
        Removes a drone from the zone's occupants.
        """
        if drone in self.occupants:
            self.occupants.remove(drone)


class ReservationTable:
    """
    Manages zone and link reservations to prevent capacity overruns.
    """

    def __init__(self) -> None:
        """
        Initializes an empty reservation table.
        """
        self.table: Dict[Tuple[str, int], int] = {}

    def reserve_zone(self, zone_name: str, turn: int) -> None:
        """
        Reserves a spot in a zone for a specific turn.
        """
        current = self.table.get((zone_name, turn), 0)
        self.table[(zone_name, turn)] = current + 1

    def is_zone_available(self, zone_name: str, turn: int,
                          max_drones: int) -> bool:
        """
        Checks if a zone has available capacity for a specific turn.
        """
        current = self.table.get((zone_name, turn), 0)
        return current < max_drones

    def reserve_link(self, z1: str, z2: str, turn: int) -> None:
        """
        Reserves a spot on a link between two zones for a specific turn.
        """
        link_name = f"{min(z1, z2)}_{max(z1, z2)}"
        current = self.table.get((link_name, turn), 0)
        self.table[(link_name, turn)] = current + 1

    def is_link_available(self, z1: str, z2: str, turn: int,
                          max_link_capacity: int) -> bool:
        """
        Checks if a link has available capacity for a specific turn.
        """
        link_name = f"{min(z1, z2)}_{max(z1, z2)}"
        current = self.table.get((link_name, turn), 0)
        return current < max_link_capacity
