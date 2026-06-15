_This project has been created as part of the 42 curriculum by tlaghzal._

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

Creates a virtual environment and installs `webcolors` for terminal colors.

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

### Check output (collision test)

```bash
make check map=maps/hard/02_capacity_hell.txt
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
├── main.py           # FlyInApp entry point
├── parser.py         # Hub, Connection, Parser
├── graph.py          # GraphNetwork
├── algo.py           # PathFinder (space-time search)
├── reservation.py    # ReservationTable
├── simulation.py     # Colored turn-by-turn output
├── check_output.py   # OutputChecker (collision test)
├── Makefile
├── setup.cfg         # flake8 config
├── mypy.ini          # mypy config
└── maps/             # Test maps
```

## Algorithm design

### Overview

The routing pipeline has four steps:

1. **Parse** the map file (`Parser`)
2. **Build** an undirected graph (`GraphNetwork`)
3. **Route** each drone with a space-time search (`PathFinder`)
4. **Print** the simulation turn by turn (`Simulation`)

### PathFinder

For each drone, paths are computed one after another. Each new path is reserved
in a shared `ReservationTable` so later drones avoid conflicts.

**Reachability:** before searching, a reverse BFS from the goal marks every hub
that can still reach the end. Search never expands into dead-end zones.

**Space-time search:** a min-heap explores states `(zone, turn)`. The cost is
the number of turns spent. From each state the algorithm can:

- Move to a neighbor (1 turn normally, 2 turns when the destination is restricted)
- Wait one turn in the same zone (only if neighbors toward the goal exist)

**Priority zones:** neighbors are sorted so `priority` hubs are tried before
`normal`, then `restricted`.

**Multiple paths:** already-used zones and links receive a small congestion
penalty. This pushes later drones toward alternative routes when several paths
have similar cost.

**Capacity checks:** before accepting a move, the algorithm verifies:

- Destination zone capacity at the arrival turn
- Link capacity while the drone is on the connection
- Start and end zone exceptions from the subject

**Waiting limit:** waiting is capped so the search cannot run forever when no
path exists.

**Reservation:** after a path is found, `_reserve` writes zone and link usage
into the table. Restricted destination moves print a connection step first
(`a-b`), then the destination zone on the next turn.

### Complexity

- One drone search: roughly O(states × log(states)) with states bounded by
  hubs × turns
- All drones: multiplied by the number of drones D
- Memory: reservation table grows with reserved `(zone/link, turn)` pairs

## Visual representation

Moves are printed as `D<id>-<zone>` or `D<id>-<from>-<to>` during restricted
transit. Colors come from the hub `color=` metadata using ANSI escape codes.
The special value `rainbow` cycles colors per character.

Drones that wait in place are omitted from that turn's line. Drones that reach
the end zone are marked delivered and no longer tracked.

Example:

```
D1-hello
D1-waypoint2 D2-hello
D1-goal D2-waypoint2
D2-goal
```

## Performance benchmarks

Measured output line count (= total simulation turns):

| Map                                | Drones | Turns | Subject target |
| ---------------------------------- | ------ | ----- | -------------- |
| easy/01_linear_path                | 2      | 4     | ≤ 6            |
| easy/02_simple_fork                | 4      | 4     | ≤ 8            |
| easy/03_basic_capacity             | 4      | 4     | ≤ 6            |
| medium/01_dead_end_trap            | 5      | 8     | ≤ 12           |
| medium/02_circular_loop            | 6      | 15    | ≤ 15           |
| medium/03_priority_puzzle          | 5      | 7     | ≤ 12           |
| hard/01_maze_nightmare             | 8      | 13    | ≤ 30           |
| hard/02_capacity_hell              | 12     | 16    | ≤ 35           |
| hard/03_ultimate_challenge         | 15     | 26    | ≤ 45           |
| challenger/01_the_impossible_dream | 25     | 43    | ≤ 45 (record)  |

## Technical choices

- **OOP:** each major task has its own class (see project structure)
- **No graph libraries:** custom adjacency list in `GraphNetwork`
- **Type hints + mypy:** all functions typed; `make lint` runs flake8 and mypy
- **Errors:** parser prints line number and reason; routing raises if a drone
  has no valid path

## Resources

- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Python typing](https://docs.python.org/3/library/typing.html)
- [Python heapq](https://docs.python.org/3/library/heapq.html)
- [flake8](https://flake8.pycqa.org/)
- [mypy](http://mypy-lang.org/)
- [webcolors](https://webcolors.readthedocs.io/)

## AI usage

AI was used to help with documentation, debugging, and code review. All code
was tested on the provided maps and checked with flake8/mypy before use.

## License

This project is created for educational purposes as part of the 42 curriculum.
