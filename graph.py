"""Graph built from hubs and connections."""

from typing import Dict, List, Optional, Tuple

from parser import Connection, Hub


class GraphNetwork:
    """Stores hubs, neighbors, and link data."""

    def __init__(self) -> None:
        """Create an empty graph."""
        self.neighbors: Dict[str, List[str]] = {}
        self.edges: Dict[Tuple[str, str], Connection] = {}
        self.hubs: Dict[str, Hub] = {}

    def create_graph(
        self, hubs: Dict[str, Hub], connections: List[Connection]
    ) -> None:
        """Fill the graph from parsed map data."""
        self.hubs = hubs
        for hub in hubs.values():
            self.neighbors[hub.name] = []

        for conn in connections:
            self.neighbors[conn.from_hub].append(conn.to_hub)
            self.neighbors[conn.to_hub].append(conn.from_hub)
            key = (
                min(conn.from_hub, conn.to_hub),
                max(conn.from_hub, conn.to_hub),
            )
            self.edges[key] = conn

    def get_neighbor(self, zone: str) -> List[Hub]:
        """Return reachable neighbor hubs (skip blocked zones)."""
        if self.hubs[zone].zone == "blocked":
            return []

        result: List[Hub] = []
        for name in self.neighbors.get(zone, []):
            if self.hubs[name].zone != "blocked":
                result.append(self.hubs[name])
        return result

    def get_connection(self, z1: str, z2: str) -> Optional[Connection]:
        """Return the connection between two hubs, if it exists."""
        key = (min(z1, z2), max(z1, z2))
        return self.edges.get(key)
