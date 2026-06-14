import subprocess
import sys
import re
from typing import Dict


def parse_output_line(line: str) -> Dict[int, str]:
    """
    Parses a turn line into a dict of drone_id -> current_location.
    """
    if not line.strip():
        return {}

    # Aggressive regex to scrub ALL terminal escape codes
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    clean_line = ansi_escape.sub("", line)

    tokens = clean_line.strip().split()
    turn_state = {}

    for token in tokens:
        if "-" not in token:
            continue

        # Now token is perfectly clean text like: "D1-gate_hell1"
        drone_part, loc_part = token.split("-", 1)

        try:
            drone_id = int(drone_part.replace("D", "").strip())
            turn_state[drone_id] = loc_part.strip()
        except ValueError:
            # Skip structural noise if any remains
            continue

    return turn_state


def verify_simulation_output(map_path: str) -> None:
    """
    Runs the simulation and verifies that no collisions occur.
    """
    print(f"Checking outputs for map: {map_path}...")

    # 1. Capture the actual standard output stream from your project runner
    cmd = ["python3", "main.py", map_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        print(f"❌ Execution crashed! Code {result.returncode}")
        print(result.stderr)
        return

    lines = result.stdout.strip().split("\n")
    print(f"Processing {len(lines)} execution frames...")

    # 2. Tracks across history
    for turn_idx, line in enumerate(lines, start=1):
        positions = parse_output_line(line)
        if not positions:
            continue

        # Check A: Collision Guard
        seen_zones: Dict[str, int] = {}
        for drone_id, zone in positions.items():
            # If it's a structural connector string like 'A-B',
            # it's in a link state
            if "-" in zone:
                continue

            if zone in seen_zones:
                print(f"❌ COLLISION AT TURN {turn_idx}: "
                      f"Drone {drone_id} and Drone {seen_zones[zone]} "
                      f"are both in '{zone}'!")
                return
            seen_zones[zone] = drone_id

    print("✅ All checks complete! No spatial conflicts detected.")


if __name__ == "__main__":
    target_map = (sys.argv[1] if len(sys.argv) > 1 else
                  "maps/challenger/01_the_impossible_dream.txt")
    verify_simulation_output(target_map)
