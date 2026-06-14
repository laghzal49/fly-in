"""Entry point for the fly-in drone routing project."""

import sys

from algo import PathFinder
from graph import GraphNetwork
from parser import Parser
from simulation import Simulation
from zone import ReservationTable


class FlyInApp:
    """Runs the full program: parse map, find paths, simulate."""

    def __init__(self, map_file: str) -> None:
        """Store the map file path."""
        self.map_file = map_file

    def run(self) -> None:
        """Parse input, build graph, route drones, print moves."""
        parser = Parser()
        try:
            parser.starter_parsing(self.map_file)
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        if parser.start_hub is None or parser.end_hub is None:
            print("Error: Missing start or end hub", file=sys.stderr)
            sys.exit(1)

        graph = GraphNetwork()
        graph.create_graph(parser.hubs, parser.connections)

        table = ReservationTable()
        finder = PathFinder(graph, table)
        try:
            paths = finder.assign_all_paths(
                parser.start_hub.name,
                parser.end_hub.name,
                parser.nb_drones,
            )
        except ValueError as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        sim = Simulation(paths, parser.end_hub.name, parser.hubs)
        sim.run()


def main() -> None:
    """Check arguments and start the application."""
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>", file=sys.stderr)
        sys.exit(1)

    FlyInApp(sys.argv[1]).run()


if __name__ == "__main__":
    main()
