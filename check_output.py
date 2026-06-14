"""Check simulation output for zone capacity violations."""

import re
import subprocess
import sys
from typing import Dict, Set

from parser import Parser


class OutputChecker:
    """Run the simulator and verify zone/link capacity rules."""

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
        """Run main.py and return True if no capacity violation."""
        print(f"Checking {self.map_path}...")

        parser = Parser()
        try:
            parser.starter_parsing(self.map_path)
        except Exception as err:
            print(f"Error parsing map: {err}")
            return False

        zone_caps: Dict[str, int] = {}
        start_name = ""
        end_name = ""
        if parser.start_hub:
            start_name = parser.start_hub.name
        if parser.end_hub:
            end_name = parser.end_hub.name
        for name, hub in parser.hubs.items():
            zone_caps[name] = hub.max_drones

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
        positions: Dict[int, str] = {}
        delivered: Set[int] = set()
        nb_drones = parser.nb_drones

        # All drones start at start_hub
        for d in range(1, nb_drones + 1):
            positions[d] = start_name

        ok = True
        for turn, line in enumerate(lines, 1):
            moves = self.parse_line(line)

            # Apply moves
            for drone_id, zone in moves.items():
                if drone_id in delivered:
                    print(
                        f"Turn {turn}: D{drone_id} moved "
                        f"after delivery"
                    )
                    ok = False
                positions[drone_id] = zone

            # Check zone occupancy (exclude drones in transit)
            zone_count: Dict[str, int] = {}
            for drone_id, zone in positions.items():
                if drone_id in delivered:
                    continue
                if "-" in zone:
                    continue
                zone_count[zone] = zone_count.get(zone, 0) + 1

            for zone, count in zone_count.items():
                if zone == start_name or zone == end_name:
                    continue
                cap = zone_caps.get(zone, 1)
                if count > cap:
                    print(
                        f"Turn {turn}: zone '{zone}' has "
                        f"{count} drones (max {cap})"
                    )
                    ok = False

            # Mark delivered drones
            for drone_id, zone in positions.items():
                if zone == end_name and drone_id not in delivered:
                    delivered.add(drone_id)

        if len(delivered) != nb_drones:
            print(
                f"Only {len(delivered)}/{nb_drones} drones "
                f"reached the goal"
            )
            ok = False

        if ok:
            print(
                f"OK: {len(lines)} turns, "
                f"all {nb_drones} drones delivered."
            )
        return ok


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
