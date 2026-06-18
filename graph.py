"""Graph built from hubs and connections."""
from __future__ import annotations

from parser import Connection, Hub


class GraphNetwork:
    """Stores hubs, neighbors, and link data."""

    def __init__(
        self,
        hubs: dict[str, Hub],
        connections: list[Connection],
    ) -> None:
        """Create a graph from parsed map data."""
        self.hubs = hubs
        self.neighbors: dict[str, list[str]] = {}
        self.edges: dict[
            tuple[str, str], Connection
        ] = {}

        for hub in self.hubs.values():
            self.neighbors[hub.name] = []

        for conn in connections:
            src, dst = conn.from_hub, conn.to_hub
            self.neighbors[src].append(dst)
            self.neighbors[dst].append(src)
            key = (min(src, dst), max(src, dst))
            self.edges[key] = conn

    def get_neighbor(
        self, zone: str,
    ) -> list[Hub]:
        """Return neighbor hubs (skip blocked)."""
        if self.hubs[zone].zone == "blocked":
            return []
        return [
            self.hubs[name]
            for name in self.neighbors.get(zone, [])
            if self.hubs[name].zone != "blocked"
        ]

    def get_connection(
        self, z1: str, z2: str,
    ) -> Connection | None:
        """Return the connection between two hubs."""
        key = (min(z1, z2), max(z1, z2))
        return self.edges.get(key)
