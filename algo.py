from parser import Parser
from graph import Graph_network
from typing import Dict, List


class Path_finder:

    def __init__(self, graph_network: Graph_network, parser: Parser) -> None:
        self.graph = graph_network
        self.parser = parser

    def find_all_path(self) -> List[List[str]]:
        """Finds the single shortest physical route from start to end."""
        start = self.parser.start_hub.name
        end = self.parser.end_hub.name

        # The queue tracks: [ [path_so_far_list] ]
        queue: List[List[str]] = [[start]]
        visited: Set[str] = {start}

        while queue:
            # Take the first path out of the queue line
            current_path = queue.pop(0)
            current_node = current_path[-1]

            # If we reached the goal, wrap it inside a outer list and return it!
            if current_node == end:
                return [current_path]

            # Look up adjacent zones from our graph adjacency matrix
            neighbors = self.graph.adj.get(current_node, [])
            
            for neighbor in neighbors:
                # Rule 1: Skip if we have already visited this zone
                if neighbor in visited:
                    continue

                # Rule 2: Skip if the map file lists this zone as explicitly blocked
                if self.parser.hubs[neighbor].zone == "blocked":
                    continue

                # Lock the node as visited, extend our path list, and add to the queue line
                visited.add(neighbor)
                queue.append(current_path + [neighbor])

        return []  # Return an empty list container if no valid route is found
