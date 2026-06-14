from typing import Dict, List, Tuple, Optional
import webcolors
from parser import Hub


class Simulation:
    """
    Handles the execution and visualization of the drone simulation.
    """

    def __init__(
        self,
        paths: Dict[int, List[Tuple[str, int]]],
        end_zone: str,
        hubs: Dict[str, Hub],
    ) -> None:
        """
        Initializes the simulation with paths, end zone, and hub information.
        """
        self.paths = paths
        self.end_zone = end_zone
        self.RESET = "\033[0m"
        self.hubs = hubs
        self.RAINBOW = [
            "\033[38;5;197m",  # Neon Pink
            "\033[38;5;46m",   # Neon Green
            "\033[38;5;226m",  # Bright Yellow
            "\033[38;5;51m",   # Bright Cyan
            "\033[38;5;135m",  # Neon Purple
            "\033[38;5;208m",  # Neon Orange
        ]

    def _get_color(self, color_name: Optional[str]) -> str:
        """
        Translates named colors to TrueColor ANSI escape sequences.
        """
        if not color_name or color_name.lower() in (
            "none", "normal", "", "rainbow"
        ):
            return ""
        try:
            rgb = webcolors.name_to_rgb(color_name.lower())
            return f"\033[38;2;{rgb.red};{rgb.green};{rgb.blue}m"
        except ValueError:
            return ""

    def _get_hub_color_name(self, zone_name: str) -> Optional[str]:
        """
        Extracts the configured color name from the current target hub.
        """
        if "-" in zone_name:
            dest_zone = zone_name.split("-")[1]
            if dest_zone in self.hubs:
                return self.hubs[dest_zone].color
        elif zone_name in self.hubs:
            return self.hubs[zone_name].color
        return None

    def _apply_rainbow_matrix(self, base_text: str, drone_id: int) -> str:
        """
        Cycles every character in the string through alternating neon codes.
        """
        colored_text = ""
        for i, char in enumerate(base_text):
            color_code = self.RAINBOW[(drone_id + i) % len(self.RAINBOW)]
            colored_text += f"{color_code}{char}{self.RESET}"
        return colored_text

    def _format_move_string(self, base_text: str,
                            color_name: Optional[str],
                            drone_id: int) -> str:
        """
        Determines if text should be rendered as raw, solid color, or rainbow.
        """
        if color_name and color_name.lower() == "rainbow":
            return self._apply_rainbow_matrix(base_text, drone_id)

        color = self._get_color(color_name)
        if color:
            return f"{color}{base_text}{self.RESET}"
        return base_text

    def run(self) -> None:
        """
        Executes the simulation and prints the moves for each turn.
        """
        if not self.paths:
            return
        valid_paths = [p for p in self.paths.values() if p]
        if not valid_paths:
            return

        # track last known zone per drone
        prev_zone: Dict[int, str] = {}
        for drone_id, path in self.paths.items():
            prev_zone[drone_id] = path[0][0]  # start zone

        max_turn = max(p[-1][1] for p in valid_paths)
        for turn in range(1, max_turn + 1):
            moves = []
            for drone_id, path in self.paths.items():
                for zone_name, zone_turn in path:
                    if zone_turn != turn:
                        continue
                    # skip if same zone as previous (waiting)
                    if zone_name == prev_zone[drone_id]:
                        break
                    prev_zone[drone_id] = zone_name
                    color_name = self._get_hub_color_name(zone_name)
                    base_text = f"D{drone_id}-{zone_name}"
                    formatted_move = self._format_move_string(
                        base_text, color_name, drone_id
                    )
                    moves.append(formatted_move)
                    break
            if moves:
                print(" ".join(moves))
