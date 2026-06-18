# File 4: simulation.py + main.py — Simulation, FlyInApp

## Class: Simulation

**What it is:** Replays computed paths and prints drone moves per turn.

```python
Simulation(drones: list[Drone], end_zone: str, hubs: dict[str, Hub])
```

**State:**
- `self.drones` — all drones with assigned paths
- `self.end_zone` — name of the goal zone
- `self.hubs` — hub metadata (for colors)

### Methods

**`_last_turn()`** — returns `max(d.last_turn for d in self.drones)`.
This is the total number of simulation turns.

**`_color_for(step)`** — looks up the ANSI color code for a step's zone.
Skips colors "none", "normal", and empty strings.

```python
COLORS = {"RED": "\033[91m", "GREEN": "\033[92m", ...}
```

**Why a separate color method?** Extracted from `_format` for clarity.
One method finds the color, another builds the string.

**`_format(drone, step)`** — builds one printable move like `D1-roof1`
or `D1-\033[91mroof1\033[0m` (with ANSI color).

**`_moves_at_turn(turn, last_move, delivered)`** — the core logic:

```python
for each drone (skip delivered):
    find the step at this turn
    if step.label == last_move[drone_id]:
        skip (drone didn't move)
    else:
        record the move
        if reached end_zone: mark delivered
```

**Why `last_move` dict?**

Drones that stay in place should be omitted from output (subject rule).
`last_move` tracks each drone's previous position. If the label hasn't
changed, the drone didn't move → skip it.

**Why `delivered` set?**

Once a drone reaches the end zone, it's "delivered" and no longer
tracked. Without this, delivered drones would show up on every
subsequent turn.

**`run()`** — the main loop:

```python
for turn in range(1, last_turn + 1):
    if all delivered: break
    moves = _moves_at_turn(turn, ...)
    if moves: print(" ".join(moves))
```

### Output format (from subject VII.5)

```
D1-roof1 D2-corridorA       ← zone moves
D1-hub-roof1                 ← restricted transit (connection label)
```

- One line per turn
- Space-separated moves
- `D<ID>-<zone>` or `D<ID>-<connection>`
- Stationary drones omitted
- Delivered drones no longer tracked

---

## Class: FlyInApp

**What it is:** The entry point. Wires everything together.

```python
FlyInApp(map_file: str)
```

**`run()` does 4 things:**

```python
1. parser.starter_parsing(self.map_file)  → MapData
2. GraphNetwork(hubs, connections)         → graph
3. PathFinder(graph).assign_all_paths(...) → drones
4. Simulation(drones, end, hubs).run()     → stdout
```

**Error handling:**
- Parse errors → caught by `except Exception`, printed to stderr
- Routing errors → caught by `except ValueError` ("No path for drone D5")

**Why a class and not just a function?**

The subject says "completely object-oriented." Also, if you need to add
flags later (like `--capacity-info`), the class can store them as
attributes without changing the method signatures.

---

## `main()` function

```python
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>", file=sys.stderr)
        sys.exit(1)
    FlyInApp(sys.argv[1]).run()
```

Simple CLI: one argument (map file path), no flags.

---

## How to add `--capacity-info` (eval task)

If asked during eval to add a capacity display flag:

**1. main.py** — split args and flags:
```python
args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = [a for a in sys.argv[1:] if a.startswith("--")]
FlyInApp(args[0], capacity_info="--capacity-info" in flags)
```

**2. FlyInApp** — add `capacity_info` param, pass graph to Simulation.

**3. Simulation** — add `graph` and `capacity_info` params. Add method:
```python
def _print_capacity_info(self, turn):
    for hub in self.hubs.values():
        if hub.is_reserved(turn):
            print(f"  Zone {hub.name}: {hub.usage(turn)}/{hub.max_drones}")
    for conn in self.graph.edges.values():
        if conn.is_reserved(turn):
            print(f"  Connection {conn.from_hub}-{conn.to_hub}: "
                  f"{conn.usage(turn)}/{conn.max_link_capacity}")
```

**4. Call it in `run()`** after printing moves:
```python
if self.capacity_info:
    self._print_capacity_info(turn)
```

**Why this is easy:** Hub and Connection already have `usage()` and
`is_reserved()`. No new data structures needed — just read and display.
Takes ~5 minutes to implement.
