"""Print drone moves turn by turn."""
from __future__ import annotations
import webcolors
from parser import Hub

PathStep = tuple[str, int]

RAINBOW = [
    "\033[38;5;197m",
    "\033[38;5;46m",
    "\033[38;5;226m",
    "\033[38;5;51m",
    "\033[38;5;135m",
    "\033[38;5;208m",
]
RESET = "\033[0m"


class Simulation:
    """Replay computed paths and print visible drone moves."""

    def __init__(
        self,
        paths: dict[int, list[PathStep]],
        end_zone: str,
        hubs: dict[str, Hub],
    ) -> None:
        """Store paths, end zone, and hub metadata."""
        self.paths: dict[int, list[PathStep]] = paths
        self.end_zone: str = end_zone
        self.hubs: dict[str, Hub] = hubs

    def _last_turn(self) -> int:
        """Return the last turn used by any path."""
        if not self.paths:
            return 0
        return max(path[-1][1] for path in self.paths.values() if path)

    def _move_color(self, move: str) -> str:
        """Return the color configured for a zone or link move."""
        zone = move.split("-", 1)[1] if "-" in move else move
        hub = self.hubs.get(zone)
        return hub.color if hub else "none"

    def _ansi_color(self, color: str) -> str:
        """Convert a color name to ANSI, or empty string if invalid."""
        if color.lower() in ("", "none", "normal"):
            return ""

        try:
            rgb = webcolors.name_to_rgb(color.lower())
        except ValueError:
            return ""

        return f"\033[38;2;{rgb.red};{rgb.green};{rgb.blue}m"

    def _rainbow(self, text: str, drone_id: int) -> str:
        """Apply rainbow colors to text."""
        result = ""
        for index, char in enumerate(text):
            color = RAINBOW[(drone_id + index) % len(RAINBOW)]
            result += f"{color}{char}{RESET}"
        return result

    def _format(self, drone_id: int, move: str) -> str:
        """Build one printable drone move."""
        text = f"D{drone_id}-{move}"
        color = self._move_color(move)

        if color.lower() == "rainbow":
            return self._rainbow(text, drone_id)

        ansi = self._ansi_color(color)
        if ansi:
            return f"{ansi}{text}{RESET}"
        return text

    def _moves_at_turn(
        self,
        turn: int,
        last_move: dict[int, str],
        delivered: set[int],
    ) -> list[str]:
        """Return all printable moves for one turn."""
        moves: list[str] = []

        for drone_id, path in self.paths.items():
            if drone_id in delivered:
                continue

            for move, move_turn in path:
                if move_turn != turn:
                    continue

                if move == last_move.get(drone_id):
                    break

                last_move[drone_id] = move
                moves.append(self._format(drone_id, move))

                if move == self.end_zone:
                    delivered.add(drone_id)
                break

        return moves

    def run(self) -> None:
        """Print one output line per turn."""
        last_move = {
            drone_id: path[0][0]
            for drone_id, path in self.paths.items()
            if path
        }
        delivered: set[int] = set()

        for turn in range(1, self._last_turn() + 1):
            if len(delivered) == len(self.paths):
                break

            moves = self._moves_at_turn(turn, last_move, delivered)
            if moves:
                print(" ".join(moves))
