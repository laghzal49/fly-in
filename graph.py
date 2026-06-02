from .parser import Hub, Connection


class Graph_network:
    def __init__(self) -> None:
        self.adj = {}
        self.weigh = {}
        
    def add_zone(self, hub:Hub) ->None:
        if hub.name not in self.adj:
            self.adj[hub.name] = []

    def add_connection(self, conn:Connection) ->None:
        if conn.to_hub not in self.adj[conn.from_hub]:
            self.adj[conn.from_hub].append(conn.to_hub)
        if conn.from_hub not in self.adj[conn.to_hub]:
            self.adj[conn.to_hub].append(conn.from_hub)
        first = min(conn.from_hub, conn.to_hub)
        second = max(conn.from_hub, conn.to_hub)
        self.weigh[first, second] = conn