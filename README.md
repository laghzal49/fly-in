*This project has been created as part of the 42 curriculum by tlaghzal.*

# Fly-in: Drone Routing System


## Description

Fly-in is an efficient drone routing system that navigates multiple autonomous drones through connected zones while minimizing simulation turns and handling complex movement constraints. The project implements advanced pathfinding algorithms that distribute drones across multiple paths, avoid conflicts, and optimize throughput in dynamic networks.

### Objective

The goal is to route a fleet of drones from a central hub (start) to a target location (end) in the fewest possible simulation turns while respecting:
- Zone capacity constraints (max_drones)
- Connection capacity constraints (max_link_capacity)
- Zone type movement costs (normal: 1 turn, restricted: 2 turns, priority: 1 turn)
- Blocked zones (inaccessible areas)

## Instructions

### Installation

```bash
make install
```

This installs the required dependencies (currently `webcolors` for terminal color support).

### Running the Simulator

To run the simulator with a test map:

```bash
make run
```

Or directly with a specific map file:

```bash
python3 main.py <path_to_map_file>
```

Example with all provided test maps:

```bash
python3 main.py maps/easy/01_linear_path.txt
python3 main.py maps/easy/02_simple_fork.txt
python3 main.py maps/medium/01_dead_end_trap.txt
python3 main.py maps/hard/01_maze_nightmare.txt
```

### Debugging

To run in debug mode with Python's built-in debugger:

```bash
make debug
```

### Code Quality

Lint and type check the codebase:

```bash
make lint           # Standard checks
make lint-strict    # Strict mypy checks
```

### Cleanup

Remove temporary files and caches:

```bash
make clean
```

## Project Structure

```
.
├── main.py           # Entry point orchestrating the simulation
├── parser.py         # Map file parser (Hub, Connection, and validation)
├── graph.py          # Graph network structure (GraphNetwork class)
├── algo.py           # Pathfinding algorithm (PathFinder with space-time Dijkstra)
├── simulation.py     # Simulation runner with colored terminal output
├── zone.py           # Zone management and reservation tracking
├── Makefile          # Build and task automation
├── README.md         # This file
└── maps/             # Test maps directory
    ├── easy/         # Easy difficulty maps
    ├── medium/       # Medium difficulty maps
    ├── hard/         # Hard difficulty maps
    └── challenger/   # Optional challenger maps
```

## Algorithm Design

### Space-Time Dijkstra with Dynamic Traffic Balancing

The pathfinding algorithm uses a novel space-time Dijkstra approach combined with dynamic traffic balancing:

1. **Backward Distance Precomputation**: Initially computes shortest distances from all hubs to the end zone using standard Dijkstra on the unweighted graph.

2. **Forward Space-Time Search**: For each drone, performs a Dijkstra search in the space-time domain (zone, turn):
   - State: (zone, turn)
   - Cost: turn count + congestion penalties
   - Prevents backward movement (ensures progress toward goal)

3. **Conflict Resolution**:
   - Zone capacity checking: Verifies no zone exceeds its max_drones limit
   - Connection capacity checking: Ensures link utilization stays within max_link_capacity
   - Reservation table: Tracks all drone movements for conflict avoidance

4. **Dynamic Traffic Balancing**:
   - Global usage penalties: Penalizes frequently used zones to distribute drones across paths
   - Look-ahead mechanism: Checks future zone availability to prevent deadlocks
   - Adaptive congestion: Uses historical drone usage to guide path selection

5. **Multi-Turn Movement Handling**:
   - Restricted zones cost 2 turns to enter
   - Priority zones receive lower sorting cost but same 1-turn movement
   - Connections properly tracked during multi-turn transitions

### Performance Characteristics

- **Time Complexity**: O(D * E * T * log(V * T)) where:
  - D = number of drones
  - E = number of edges
  - T = simulation turns
  - V = number of vertices

- **Space Complexity**: O(V * T) for reservation table storage

- **Optimization Strategies**:
  - Early path computation prevents recalculation
  - Single-pass reservation avoids replay
  - Congestion penalties guide drones to less-traveled paths
  - Prevents deadlocks through capacity-aware scheduling

### Performance Benchmarks Achieved

- **Easy Maps**: Target ≤ 10 turns
  - Linear path (2 drones): 4 turns ✓
  - Simple fork (4 drones): 4 turns ✓

- **Medium Maps**: Target 10-30 turns
  - Dead end trap: Within target
  - Circular loop: Within target

- **Hard Maps**: Target < 60 turns
  - All hard maps solvable

## Visual Representation

### Terminal Color Output

The simulator provides colored terminal output showing drone movements:

```
D1-waypoint1 D2-start
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Colors are automatically assigned based on zone metadata:
- Green for start zones
- Red for end/goal zones
- Blue for waypoints
- Gray for obstacles
- Custom colors as specified in map files

### Output Format

Each simulation turn is printed as a single line containing:
- Drone identifier: `D<id>` (e.g., D1, D2)
- Destination: `<zone_name>` or `<connection_name>` for multi-turn movements
- Drones that don't move in a turn are omitted
- Format: `D<id>-<zone> D<id>-<zone> ...`

## Technical Choices

### Object-Oriented Design

The entire system is built with object-oriented principles:
- `Hub`: Represents zones with metadata
- `GraphNetwork`: Manages graph structure and neighbor queries
- `PathFinder`: Encapsulates pathfinding algorithm with state
- `Simulation`: Handles turn-by-turn execution and output
- `Drone`: Represents drone state and path tracking
- `Zone`: Manages occupancy and capacity
- `ReservationTable`: Tracks movements across space-time

### Type Safety

- Full type hints for all functions and variables
- mypy static type checking with `--disallow-untyped-defs`
- No untyped code paths

### Error Handling

- Graceful parsing with clear error messages
- Exception handling for file I/O operations
- Validation of map structure and parameters
- Explicit error reporting on routing deadlocks

## Constraints & Limitations

- **No external graph libraries**: Implementation uses custom graph structure
- **Python 3.10+**: Uses modern Python features (union types with `|`)
- **Flake8 compliance**: All code follows PEP 8 style guidelines
- **Type safe**: Complete type coverage with mypy

## Resources

### Graph Algorithms
- Dijkstra's Algorithm: [Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- Space-Time Pathfinding: Domain-specific optimization for temporal conflicts

### Python Documentation
- [typing module](https://docs.python.org/3/library/typing.html)
- [heapq module](https://docs.python.org/3/library/heapq.html) - Priority queue implementation
- [dataclasses](https://docs.python.org/3/library/dataclasses.html)

### Development Tools
- [flake8](https://flake8.pycqa.org/) - Style guide enforcement
- [mypy](http://mypy-lang.org/) - Static type checker
- [webcolors](https://webcolors.readthedocs.io/) - CSS color name to RGB conversion

### Related Topics
- Network flow optimization
- Temporal constraint satisfaction
- Multi-agent pathfinding
- Capacity-constrained routing

## AI Usage

AI was used to support the following aspects of the project:

1. **Documentation & Testing**:
   - Docstring generation and code comments
   - Test case design for edge cases
   - Performance benchmark planning

All AI-generated code was thoroughly reviewed, tested, and validated before integration. The core algorithm and final implementation represent original understanding and problem-solving.

## License

This project is created for educational purposes as part of the 42 curriculum.
