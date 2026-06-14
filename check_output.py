"""Check simulation output for zone collisions."""

import re
import subprocess
import sys
from typing import Dict


class OutputChecker:
    """Run the simulator and look for two drones in the same zone."""

    ANSI_RE = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    def __init__(self, map_path: str) -> None:
        """Store the map file to test."""
        self.map_path = map_path

    @staticmethod
    def parse_line(line: str) -> Dict[int, str]:
        """Read one output line into drone_id -> zone."""
        if not line.strip():
            return {}

        clean = OutputChecker.ANSI_RE.sub("", line)
        result: Dict[int, str] = {}

        for token in clean.strip().split():
            if "-" not in token:
                continue
            drone_str, zone = token.split("-", 1)
            try:
                drone_id = int(drone_str.replace("D", ""))
                result[drone_id] = zone
            except ValueError:
                continue
        return result

    def run(self) -> bool:
        """Run main.py and return True if no collision is found."""
        print(f"Checking {self.map_path}...")

        res = subprocess.run(
            [sys.executable, "main.py", self.map_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            print(f"Error: program exited with {res.returncode}")
            print(res.stderr)
            return False

        lines = res.stdout.strip().split("\n")
        for turn, line in enumerate(lines, 1):
            positions = self.parse_line(line)
            used: Dict[str, int] = {}
            for drone_id, zone in positions.items():
                if "-" in zone:
                    continue
                if zone in used:
                    other = used[zone]
                    print(
                        f"Collision at turn {turn}: "
                        f"D{drone_id} and D{other} in {zone}"
                    )
                    return False
                used[zone] = drone_id

        print("OK: no collision found.")
        return True


def main() -> None:
    """Run the checker from the command line."""
    if len(sys.argv) > 1:
        map_path = sys.argv[1]
    else:
        map_path = "maps/challenger/01_the_impossible_dream.txt"

    checker = OutputChecker(map_path)
    if not checker.run():
        sys.exit(1)


if __name__ == "__main__":
    main()
