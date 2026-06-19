"""Print drone moves turn by turn."""
from __future__ import annotations

from parser import Hub, MapData
from reservation import ReservationTable

PathStep = tuple[str, int]
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
        paths: dict[int, list[PathStep]],
        maps: MapData,
        table: ReservationTable | None = None,
        capacity_info: bool = False,
    ) -> None:
        """Store paths, end zone, hub metadata, and capacity-info deps."""
        self.paths: dict[int, list[PathStep]] = paths
        self.end_zone: str = maps.end_hub.name
        self.hubs: dict[str, Hub] = maps.hubs
        self.connections = maps.connections
        self.table = table
        self.capacity_info = capacity_info

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
        return COLORS.get(color.upper(), "")

    def _format(self, drone_id: int, move: str) -> str:
        """Build one printable drone move."""
        text = f"{move}"
        color = self._move_color(move)
        ansi = self._ansi_color(color)
        if ansi:
            return f"D{drone_id}-{ansi}{text}{RESET}"
        return f"D{drone_id}-{text}"

    def _link_capacity(self, src: str, dst: str) -> int:
        """Return the max capacity configured for a link, or 0."""
        for conn in self.connections:
            if {conn.from_hub, conn.to_hub} == {src, dst}:
                return conn.max_link_capacity
        return 0

    def _print_capacity(self, move: str, turn: int) -> None:
        """Print zone or link capacity usage for one active move."""
        if not self.table:
            return
        if "-" in move:
            src, dst = move.split("-", 1)
            used = self.table.link_count(src, dst, turn)
            limit = self._link_capacity(src, dst)
            print(f"Connection {move}: {used}/{limit} capacity used")
        else:
            used = self.table.zone_count(move, turn)
            limit = self.hubs[move].max_drones if move in self.hubs else 0
            print(f"Zone {move}: {used}/{limit} drones")

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

                if self.capacity_info:
                    self._print_capacity(move, turn)

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
