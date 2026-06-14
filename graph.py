from parser import Hub, Connection
from typing import List, Dict, Tuple, Optional


class GraphNetwork:
    """
    Represents the network of hubs and connections as a graph.
    """

    def __init__(self) -> None:
        """
        Initializes an empty graph network.
        """
        self.neighbors: Dict[str, List[str]] = {}
        self.edges: Dict[Tuple[str, str], Connection] = {}
        self.hubs: Dict[str, Hub] = {}

    def create_graph(
        self, hubs: Dict[str, Hub], connections: List[Connection]
    ) -> None:
        """
        Builds the graph from the provided hubs and connections.
        """
        self.hubs = hubs
        for hub in hubs.values():
            self.neighbors[hub.name] = []
        for conn in connections:
            self.neighbors[conn.from_hub].append(conn.to_hub)
            self.neighbors[conn.to_hub].append(conn.from_hub)
            key = (min(conn.from_hub, conn.to_hub),
                   max(conn.from_hub, conn.to_hub))
            self.edges[key] = conn

    def get_neighbor(self, zone: str) -> List[Hub]:
        """
        Returns a list of accessible neighbor hubs for a given zone.
        """
        if self.hubs[zone].zone == "blocked":
            return []
        return [
            self.hubs[n] for n in self.neighbors.get(zone, [])
            if self.hubs[n].zone != "blocked"
        ]

    def get_connection(
        self, z1: str, z2: str
    ) -> Optional[Connection]:
        """
        Returns the connection object between two zones, if it exists.
        """
        key = (min(z1, z2), max(z1, z2))
        return self.edges.get(key)
