import sys

# Import your custom modules explicitly
from parser import Parser
from graph import Graph_network
from algo import Path_finder
from simlution import Simlution


def main() -> None:
    """The central entry point execution script."""
    # Step 1: Ensure the user provided a map file in the command line
    if len(sys.argv) != 2:
        print("Usage: python3 -m directory_name.main <path_to_map_file>", file=sys.stderr)
        sys.exit(1)

    map_filepath = sys.argv[1]

    # Step 2: Initialize the map parser and read the file
    parser = Parser()
    try:
        parser.starter_parsing(map_filepath)
    except Exception as error:
        print(f"Error parsing map file: {error}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Build the graph structure using the parsed data
    graph = Graph_network()
    
    for hub in parser.hubs.values():
        graph.add_zone(hub)
        
    for connection in parser.connections:
        graph.add_connection(connection)

    # Step 4: Run the ultra-simple pathfinder to get the path
    pathfinder = Path_finder(graph, parser)
    paths = pathfinder.find_all_path()

    if not paths:
        print("Fatal Error: No valid path found from start to end.", file=sys.stderr)
        sys.exit(1)

    # Step 5: Run the ultra-simple greedy simulation loop
    sim = Simlution(graph, parser, paths)
    sim.simulate()


if __name__ == "__main__":
    main()
