# Fly-in — Documentation index

Per-file architecture notes for the project. Start with the global overview
in [../ARCHITECTURE.md](../ARCHITECTURE.md), then read each module below.

## Source files

| File              | Document                           | Role                                  |
| ----------------- | ---------------------------------- | ------------------------------------- |
| `main.py`         | [main.md](main.md)                 | Entry point and orchestration         |
| `parser.py`       | [parser.md](parser.md)             | Map file parsing and validation       |
| `graph.py`        | [graph.md](graph.md)               | Graph structure (hubs + links)        |
| `reservation.py`  | [reservation.md](reservation.md)   | Reservation table (capacity tracking) |
| `algo.py`         | [algo.md](algo.md)                 | Pathfinding for all drones            |
| `simulation.py`   | [simulation.md](simulation.md)     | Colored terminal output               |
| `check_output.py` | [check_output.md](check_output.md) | Collision checker (test tool)         |

## Reading order (recommended)

1. [main.md](main.md) — see the full pipeline
2. [parser.md](parser.md) — understand map input
3. [graph.md](graph.md) — how zones connect
4. [reservation.md](reservation.md) — how conflicts are avoided
5. [algo.md](algo.md) — routing algorithm (most important for eval)
6. [simulation.md](simulation.md) — output format
7. [check_output.md](check_output.md) — optional testing

## Pipeline (quick view)

```
main.py
  → parser.py    (read map)
  → graph.py     (build network)
  → reservation.py (empty table)
  → algo.py      (find + reserve paths)
  → simulation.py (print moves)
```
