"""Print drone moves turn by turn."""
from __future__ import annotations

from drone import Drone, MoveStep
from parser import Hub

RESET = "\033[0m"
COLORS = {
    "BLACK": "\033[30m",
    "RED": "\033[91m",
    "WHITE": "\033[97m",
    "GOLD": "\033[38;5;220m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "DARKRED": "\033[38;5;88m",
    "CRIMSON": "\033[38;2;220;20;60m",
    "LIME": "\033[38;5;118m",
    "BLUE": "\033[94m",
    "BROWN": "\033[38;5;94m",
    "MAROON": "\033[38;2;192;128;129m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "ORANGE": "\033[38;5;208m",
    "PURPLE": "\033[38;5;93m",
    "DEFAULT": "\033[0m",
    "VIOLET": "\033[38;5;177m",
}


class Simulation:
    """Replay computed paths and print visible drone moves."""

    def __init__(
        self,
        drones: list[Drone],
        end_zone: str,
        hubs: dict[str, Hub],
    ) -> None:
        """Store drones, end zone, and hub metadata."""
        self.drones = drones
        self.end_zone = end_zone
        self.hubs = hubs

    def _last_turn(self) -> int:
        """Return the last turn used by any drone."""
        if not self.drones:
            return 0
        return max(d.last_turn for d in self.drones)

    def _color_for(self, step: MoveStep) -> str:
        """Return the ANSI color for a step, or empty."""
        zone = step.dst if step.is_link else step.zone
        hub = self.hubs.get(zone) if zone else None
        color = hub.color if hub else "none"
        skip = ("", "none", "normal")
        if color.lower() in skip:
            return ""
        return COLORS.get(color.upper(), "")

    def _format(
        self, drone: Drone, step: MoveStep,
    ) -> str:
        """Build one printable drone move."""
        ansi = self._color_for(step)
        if ansi:
            return (
                f"{drone.name}-"
                f"{ansi}{step.label}{RESET}"
            )
        return f"{drone.name}-{step.label}"

    def _moves_at_turn(
        self,
        turn: int,
        last_move: dict[int, str],
        delivered: set[int],
    ) -> list[str]:
        """Collect all printable moves for one turn."""
        moves: list[str] = []

        for drone in self.drones:
            if drone.drone_id in delivered:
                continue

            for step in drone.path:
                if step.turn != turn:
                    continue

                # Skip if drone hasn't actually moved
                if step.label == last_move.get(
                    drone.drone_id,
                ):
                    break

                last_move[drone.drone_id] = step.label
                moves.append(self._format(drone, step))

                # Mark delivered when reaching end
                if (
                    not step.is_link
                    and step.zone == self.end_zone
                ):
                    delivered.add(drone.drone_id)
                break

        return moves

    def run(self) -> None:
        """Print one output line per turn."""
        last_move = {
            d.drone_id: d.path[0].label
            for d in self.drones if d.path
        }
        delivered: set[int] = set()

        for turn in range(1, self._last_turn() + 1):
            if len(delivered) == len(self.drones):
                break

            moves = self._moves_at_turn(
                turn, last_move, delivered,
            )
            if moves:
                print(" ".join(moves))
