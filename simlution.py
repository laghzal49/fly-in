from parser import Parser
from graph import Graph_network
from typing import Dict, List


class Simlution:

    def __init__(self, graph: Graph_network, parser: Parser, paths: List[List[str]]) -> None:
        self.graph = graph
        self.parser = parser
        self.path = paths[0] 
        self.num_drones = parser.nb_drones
        self.end_name = parser.end_hub.name
        self.drone_positions: List[int] = [0] * self.num_drones
        self.zone_occupi: Dict[str, int] = {name: 0 for name in self.graph.adj}
        self.zone_occupi[self.parser.start_hub.name] = self.num_drones

    def simulate(self) -> None:
        """Runs a dead-simple loop that steps through turns until all drones reach the goal."""
        turn_count = 0
        while any(pos < len(self.path) - 1 for pos in self.drone_positions):
            turn_count += 1
            moves_this_turn: List[str] = []

            for i in range(self.num_drones):
                curr_idx = self.drone_positions[i]
                if curr_idx == len(self.path) - 1:
                    continue
                curr_zone = self.path[curr_idx]
                next_zone = self.path[curr_idx + 1]
                dest_hub = self.parser.hubs[next_zone]
                if next_zone == self.end_name or self.zone_occupi[next_zone] < dest_hub.max_drones:
                    
                    self.zone_occupi[curr_zone] -= 1
                    self.zone_occupi[next_zone] += 1
                    
                    self.drone_positions[i] += 1
                    moves_this_turn.append(f"D{i + 1}-{next_zone}")
            if moves_this_turn:
                print(" ".join(moves_this_turn))
