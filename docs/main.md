# main.py

## Purpose

Entry point of the project. Wires every module together and runs the full
pipeline: **parse → graph → route → simulate**.

## Location in the pipeline

```mermaid
flowchart LR
    A[main.py] --> B[parser.py]
    B --> C[graph.py]
    C --> D[algo.py + reservation.py]
    D --> E[simulation.py]
```

## Classes and functions

### `FlyInApp`

Main application class. One instance = one run with one map file.

| Member     | Type  | Description                    |
| ---------- | ----- | ------------------------------ |
| `map_file` | `str` | Path to the map file from argv |

| Method               | Description              |
| -------------------- | ------------------------ |
| `__init__(map_file)` | Stores the map path      |
| `run()`              | Executes all four stages |

### `main()`

Free function called when the script runs. Checks that exactly one argument
(the map file) was passed, then creates `FlyInApp` and calls `run()`.

## How `run()` works (step by step)

```
1. Parser().starter_parsing(map_file)
      → fills hubs, connections, nb_drones, start/end

2. GraphNetwork().create_graph(hubs, connections)
      → adjacency list + edge lookup

3. ReservationTable() + PathFinder(graph, table)
      → assign_all_paths(start, end, nb_drones)
      → dict {1: path, 2: path, ...}

4. Simulation(paths, end_name, hubs).run()
      → prints colored moves each turn
```

## Input / output

| In                      | Out                            |
| ----------------------- | ------------------------------ |
| Map file path (CLI arg) | Colored lines on stdout        |
|                         | Errors on stderr + exit code 1 |

## Dependencies

```python
from algo import PathFinder
from graph import GraphNetwork
from parser import Parser
from reservation import ReservationTable
from simulation import Simulation
```

## Error handling

- Parse errors → caught, printed to stderr, `sys.exit(1)`
- Missing start/end hub → message + exit
- No path for a drone → `ValueError` from `PathFinder` (not caught here)

## How to run

```bash
python3 main.py maps/easy/01_linear_path.txt
make run map=maps/easy/02_simple_fork.txt
```

## Peer eval tips

- **Q: Where does the program start?** → `main()` → `FlyInApp.run()`
- **Q: What does main.py NOT do?** → No parsing logic, no pathfinding, no
  printing — it only connects the other classes.
