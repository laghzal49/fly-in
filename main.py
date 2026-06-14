import sys
from parser import Parser
from graph import GraphNetwork
from algo import PathFinder
from simulation import Simulation
from zone import ReservationTable


class Main:
    """
    Main entry point for the drone simulation application.
    """

    def __init__(self, file_name: str) -> None:
        """
        Initializes the Main class with the input map file name.
        """
        self.file_name = file_name

    def run(self) -> None:
        """
        Orchestrates the parsing, pathfinding, and simulation execution.
        """
        parser = Parser()
        try:
            parser.starter_parsing(self.file_name)
        except Exception as error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)

        graph = GraphNetwork()
        graph.create_graph(parser.hubs, parser.connections)

        if not parser.start_hub or not parser.end_hub:
            print("Error: Missing start or end hub", file=sys.stderr)
            sys.exit(1)

        table = ReservationTable()
        pathfinder = PathFinder(graph, table)
        paths = pathfinder.assign_all_paths(
            parser.start_hub.name, parser.end_hub.name, parser.nb_drones
        )
        sim = Simulation(paths, parser.end_hub.name, parser.hubs)
        sim.run()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>", file=sys.stderr)
        sys.exit(1)

    Main(sys.argv[1]).run()
