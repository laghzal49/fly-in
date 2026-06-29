*This project has been created as part of the 42 curriculum by tlaghzal.*

# Fly-in: Drone Routing System

## Description

Fly-in routes a fleet of drones from a start zone to an end zone through a
network of connected hubs. The program parses a map file, finds conflict-free
paths for every drone, then prints each turn of the simulation with colored
terminal output.

The goal is to deliver all drones in as few turns as possible while respecting:

- Zone capacity (`max_drones`)
- Link capacity (`max_link_capacity`)
- Zone types: normal (1 turn), restricted (2 turns), priority (1 turn,
  preferred first), blocked (impassable)

## Instructions

### Installation

```bash
make install
```

Creates a virtual environment and installs dependencies.

### Running the simulator

```bash
make run
make run map=maps/easy/02_simple_fork.txt
```

Or directly:

```bash
.venv/bin/python main.py maps/easy/01_linear_path.txt
```

### Debugging

```bash
make debug map=maps/medium/01_dead_end_trap.txt
```

### Code quality

```bash
make lint
make lint-strict
```

### Cleanup

```bash
make clean
```

## Project structure

```
.
├── main.py           # FlyInApp entry point + CLI parsing
├── parser.py         # Hub, Connection, MapData, Parser
├── graph.py          # GraphNetwork (adjacency + edges)
├── drone.py          # Drone and MoveStep classes
├── algo.py           # PathFinder (space-time search)
├── simulation.py     # Colored turn-by-turn output
├── Makefile
├── setup.cfg         # flake8 config
├── mypy.ini          # mypy config
└── maps/             # Test maps (easy, medium, hard, challenger)
```

## Algorithm design

### Overview

The routing pipeline has four steps:

1. **Parse** the map file (`Parser`)
2. **Build** an undirected graph (`GraphNetwork`)
3. **Route** each drone with a space-time search (`PathFinder`)
4. **Print** the simulation turn by turn (`Simulation`)

### Object-oriented architecture

Each entity manages its own state:

- **Hub** and **Connection** track their own reservations per turn via a
  `reservations: Dict[int, int]` dict. They expose `reserve(turn)`,
  `usage(turn)`, `is_reserved(turn)`, and `is_available(turn)` methods.
- **MoveStep** encapsulates one step in a drone's path — either at a zone
  or on a link. Zone steps carry a `via` field recording which connection
  was used, so reservation logic is self-contained per step.
- **Drone** holds its identity, path, and reservation status.

This eliminates the need for any central reservation table.

### PathFinder

For each drone, paths are computed sequentially. Each path is reserved
immediately so later drones avoid conflicts.

**Reachability:** before searching, a reverse traversal from the goal marks
every hub that can reach the end. Dead-end zones are never expanded.

**Space-time search:** a min-heap explores `(zone, turn)` states. Cost is
the number of turns. From each state the algorithm can:

- Move to a neighbor (1 turn normally, 2 turns for restricted)
- Wait one turn in the same zone

**Priority zones:** neighbors are sorted so `priority` hubs are tried before
`normal`, then `restricted`.

**Capacity checks:** before accepting a move, the algorithm checks:

- Destination zone capacity at the arrival turn
- Link capacity while the drone is on the connection
- Start and end zone exceptions from the subject

**Waiting limit:** capped so the search cannot run forever when no path exists.

**Reservation:** after a path is found, `_reserve` iterates each MoveStep.
Each step is self-contained — zone steps use `step.via` for link
reservation, link steps reserve the connection directly.

### Complexity
**One Drone Search:** $O(H \cdot T \log(H \cdot T))$  
  The pathfinder explores states bounded by $H$ (the total number of **hubs**) multiplied by $T$ (the maximum turn **limit** checked during the search). The $\log$ factor comes from sorting choices within the `heapq` priority queue.
* **All Drones:** $O(D \cdot H \cdot T \log(H \cdot T))$  
  Because `assign_all_paths` calculates routes sequentially, the total time is multiplied by $D$ (the number of **drones**). Each drone routes dynamically around the reservations of previous drones.
* **Memory:** $O(H \cdot T + E \cdot T)$  
  Memory scales based on the `seen` state tracking set and the graph's reservation dictionary pairs, which grow     dynamically with active `(zone, turn)` and `(link, turn)` allocations.

## Visual representation

Moves are printed as `D<id>-<zone>` or `D<id>-<from>-<to>` during restricted
transit. Colors come from the hub `color=` metadata using ANSI escape codes.

Drones that wait in place are omitted from that turn's line. Drones that reach
the end zone are marked delivered and no longer tracked.

Example:

```
D1-hello
D1-waypoint2 D2-hello
D1-goal D2-waypoint2
D2-goal
```


### Input:
  
nb_drones: 4

start_hub: start 0 0 [color=green max_drones=4]
hub: bottleneck 1 0 [color=orange max_drones=2]
hub: wide_area 2 0 [color=blue max_drones=3]
end_hub: goal 3 0 [color=red max_drones=4]

connection: start-bottleneck [max_link_capacity=4]
connection: bottleneck-wide_area [max_link_capacity=4]
connection: wide_area-goal [max_link_capacity=4]

### Output
  D1-bottleneck D2-bottleneck
  D1-wide_area D2-wide_area D3-bottleneck D4-bottleneck
  D1-goal D2-goal D3-wide_area D4-wide_area
  D3-goal D4-goal

  
## Performance benchmarks

Measured output line count (= total simulation turns):

| Map                                | Drones | Turns | Target |
| ---------------------------------- | ------ | ----- | ------ |
| easy/01_linear_path                | 2      | 4     | ≤ 6    |
| easy/02_simple_fork                | 4      | 4     | ≤ 8    |
| easy/03_basic_capacity             | 4      | 4     | ≤ 6    |
| medium/01_dead_end_trap            | 5      | 8     | ≤ 12   |
| medium/02_circular_loop            | 6      | 15    | ≤ 15   |
| medium/03_priority_puzzle          | 5      | 7     | ≤ 12   |
| hard/01_maze_nightmare             | 8      | 13    | ≤ 30   |
| hard/02_capacity_hell              | 12     | 16    | ≤ 35   |
| hard/03_ultimate_challenge         | 15     | 26    | ≤ 45   |
| challenger/01_the_impossible_dream | 25     | 43    | ≤ 45   |

All targets met or beaten, including the challenger map.

## Technical choices

- **OOP:** each major entity has its own class with encapsulated state
- **No graph libraries:** custom adjacency list in `GraphNetwork`
- **Self-managed reservations:** Hub and Connection track their own usage
  per turn — no central table
- **Type hints + mypy:** all functions typed; `make lint` passes
- **Errors:** parser prints line number and reason; routing raises if a
  drone has no valid path

## Resources

- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Python typing](https://docs.python.org/3/library/typing.html)
- [Python heapq](https://docs.python.org/3/library/heapq.html)
- [flake8](https://flake8.pycqa.org/)
- [mypy](http://mypy-lang.org/)

## AI usage

AI was used to assist with debugging, and code review.
All generated code was reviewed, tested on all provided maps, and verified
with flake8/mypy before integration.

## License

This project is created for educational purposes as part of the 42 curriculum.
