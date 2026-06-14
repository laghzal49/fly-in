"""Print drone moves turn by turn with colors."""

from typing import Dict, List, Optional, Set, Tuple

import webcolors

from parser import Hub

PathStep = Tuple[str, int]


class Simulation:
    """Show each turn of the drone simulation in the terminal."""

    def __init__(
        self,
        paths: Dict[int, List[PathStep]],
        end_zone: str,
        hubs: Dict[str, Hub],
    ) -> None:
        """Store paths, goal zone, and hub colors."""
        self.paths = paths
        self.end_zone = end_zone
        self.hubs = hubs
        self.reset = "\033[0m"
        self.rainbow = [
            "\033[38;5;197m",
            "\033[38;5;46m",
            "\033[38;5;226m",
            "\033[38;5;51m",
            "\033[38;5;135m",
            "\033[38;5;208m",
        ]

    def _color_code(self, name: Optional[str]) -> str:
        """Convert a color name to an ANSI code."""
        if not name or name.lower() in (
            "none", "normal", "", "rainbow"
        ):
            return ""
        try:
            rgb = webcolors.name_to_rgb(name.lower())
            return (
                f"\033[38;2;{rgb.red};{rgb.green};{rgb.blue}m"
            )
        except ValueError:
            return ""

    def _hub_color(self, zone: str) -> Optional[str]:
        """Get the color set on the hub for this move."""
        if "-" in zone:
            dest = zone.split("-", 1)[1]
            if dest in self.hubs:
                return self.hubs[dest].color
        elif zone in self.hubs:
            return self.hubs[zone].color
        return None

    def _rainbow_text(self, text: str, drone_id: int) -> str:
        """Color each character with a cycling rainbow."""
        out = ""
        for i, char in enumerate(text):
            code = self.rainbow[(drone_id + i) % len(self.rainbow)]
            out += f"{code}{char}{self.reset}"
        return out

    def _format_move(
        self, text: str, color: Optional[str], drone_id: int
    ) -> str:
        """Apply solid color or rainbow to one move string."""
        if color and color.lower() == "rainbow":
            return self._rainbow_text(text, drone_id)
        code = self._color_code(color)
        if code:
            return f"{code}{text}{self.reset}"
        return text

    def _last_turn(self) -> int:
        """Find the last turn used by any drone."""
        max_turn = 0
        for path in self.paths.values():
            if path and path[-1][1] > max_turn:
                max_turn = path[-1][1]
        return max_turn

    def _is_delivered(self, zone: str) -> bool:
        """Return True when the drone has reached the end zone."""
        return zone == self.end_zone

    def run(self) -> None:
        """Print all moves from turn 1 until every drone is delivered."""
        if not self.paths:
            return

        last_zone: Dict[int, str] = {}
        delivered: Set[int] = set()
        for drone_id, path in self.paths.items():
            if path:
                last_zone[drone_id] = path[0][0]

        turn = 1
        while turn <= self._last_turn():
            if len(delivered) == len(self.paths):
                break

            moves: List[str] = []
            for drone_id, path in self.paths.items():
                if drone_id in delivered:
                    continue
                for zone, t in path:
                    if t != turn:
                        continue
                    if zone == last_zone[drone_id]:
                        break
                    last_zone[drone_id] = zone
                    text = f"D{drone_id}-{zone}"
                    color = self._hub_color(zone)
                    moves.append(
                        self._format_move(text, color, drone_id)
                    )
                    if self._is_delivered(zone):
                        delivered.add(drone_id)
                    break
            if moves:
                print(" ".join(moves))
            turn += 1
