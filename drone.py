"""Drone and MoveStep classes for the drone routing system."""

from __future__ import annotations


class MoveStep:
    """One step in a drone's path."""

    __slots__ = ("turn", "_zone", "_src", "_dst", "_via")

    def __init__(
        self,
        turn: int,
        zone: str | None = None,
        src: str | None = None,
        dst: str | None = None,
        via: tuple[str, str] | None = None,
    ) -> None:
        """Create a move step (use the class methods instead)."""
        self.turn = turn
        self._zone = zone
        self._src = src
        self._dst = dst
        self._via = via

    @classmethod
    def at_zone(cls, zone: str, turn: int,
                via: tuple[str, str] | None = None) -> MoveStep:
        """Create a step where the drone is at a zone.

        Args:
            via: optional (src, dst) of the connection used to get here.
        """
        return cls(turn=turn, zone=zone, via=via)

    @classmethod
    def on_link(cls, src: str, dst: str, turn: int) -> MoveStep:
        """Create a step where the drone is traversing a link."""
        return cls(turn=turn, src=src, dst=dst)

    @property
    def is_link(self) -> bool:
        """Return True if this step is a link traversal."""
        return self._src is not None

    @property
    def zone(self) -> str | None:
        """Return zone name, or None for link steps."""
        return self._zone

    @property
    def src(self) -> str | None:
        """Return source hub name for link steps."""
        return self._src

    @property
    def dst(self) -> str | None:
        """Return destination hub name for link steps."""
        return self._dst

    @property
    def via(self) -> tuple[str, str] | None:
        """Return the connection (src, dst) used to reach this zone, if any."""
        return self._via

    @property
    def label(self) -> str:
        """Return display string: 'zone' or 'src-dst'."""
        if self.is_link:
            return f"{self._src}-{self._dst}"
        return self._zone or ""

    def __repr__(self) -> str:
        """Show a helpful debug string."""
        if self.is_link:
            return f"MoveStep(link={self._src}->{self._dst}, t={self.turn})"
        return f"MoveStep(zone={self._zone}, t={self.turn})"

    def __lt__(self, other: object) -> bool:
        """Compare by turn for heap ordering."""
        if not isinstance(other, MoveStep):
            return NotImplemented
        return self.turn < other.turn

    def __eq__(self, other: object) -> bool:
        """Check equality by label and turn."""
        if not isinstance(other, MoveStep):
            return NotImplemented
        return self.turn == other.turn and self.label == other.label


class Drone:
    """A single drone that knows its identity, route, and reservation state."""

    def __init__(self, drone_id: int, origin: str, destination: str) -> None:
        """Create a drone with id, origin, and destination."""
        self.drone_id: int = drone_id
        self.origin: str = origin
        self.destination: str = destination
        self.path: list[MoveStep] = []
        self.reserved: bool = False

    @property
    def name(self) -> str:
        """Return the display name of this drone (e.g. 'D1')."""
        return f"D{self.drone_id}"

    @property
    def last_turn(self) -> int:
        """Return the last turn number in this drone's path."""
        if not self.path:
            return 0
        return self.path[-1].turn

    def __repr__(self) -> str:
        """Show a helpful debug string."""
        status = "reserved" if self.reserved else "pending"
        return (
            f"Drone({self.name}, {self.origin} -> {self.destination}, "
            f"{status}, steps={len(self.path)})"
        )
