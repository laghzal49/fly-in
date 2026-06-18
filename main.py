"""Entry point for the fly-in drone routing project."""

import sys

from algo import PathFinder
from graph import GraphNetwork
from parser import Parser
from simulation import Simulation


class FlyInApp:
    """Parse map, find paths, simulate."""

    def __init__(self, map_file: str) -> None:
        """Store the map file path."""
        self.map_file = map_file

    def run(self) -> None:
        """Parse input, build graph, route drones, print."""
        parser = Parser()
        try:
            map_data = parser.starter_parsing(self.map_file)
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        graph = GraphNetwork(
            map_data.hubs, map_data.connections,
        )
        finder = PathFinder(graph)
        try:
            drones = finder.assign_all_paths(
                map_data.start_hub.name,
                map_data.end_hub.name,
                map_data.nb_drones,
            )
        except ValueError as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        Simulation(
            drones, map_data.end_hub.name, map_data.hubs,
        ).run()


def main() -> None:
    """Check arguments and start the application."""
    if len(sys.argv) != 2:
        print(
            "Usage: python3 main.py <map_file>",
            file=sys.stderr,
        )
        sys.exit(1)

    FlyInApp(sys.argv[1]).run()


if __name__ == "__main__":
    main()
