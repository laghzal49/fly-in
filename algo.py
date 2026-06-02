from sre_compile import dis

from .parser import Hub, Connection, Parser
from .graph import Graph_network

class Path_finder():
    def __init__(self, graph_network: Graph_network, parser:Parser) -> None:
        self.graph = graph_network
        self.parser = parser

    def get_zone_cost(self, zone_name: str)->int:
        costs = {"normal": 1, "priority": 1, "restricted": 2, "blocked": 999999999999}
        zone = self.parser.hubs[zone_name].zone
        return costs[zone]

    def score_calcule(self):
            distances = {}
            for every_hub in self.graph.adj:
                distances[every_hub] = float('inf')
            if self.parser.end_hub is None:
                raise ValueError("Topology Error: No end_hub defined in the map file.")
            end_node = self.parser.end_hub.name
            distances[end_node] = 0
            queue = [end_node]
            while queue:
                current_node = queue.pop(0)
                for neighbor in self.graph.adj[current_node]:
                    score = distances[current_node] + self.get_zone_cost(neighbor)
                    if score < distances[neighbor]:
                        distances[neighbor] = score
                        queue.append(neighbor)
                return distances