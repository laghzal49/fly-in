# File 2: drone.py — MoveStep, Drone

## Overview

`drone.py` defines the data objects that represent a drone and its
planned movements. Two classes: **MoveStep** (one step) and **Drone**
(one drone with a list of steps).

---

## Class: MoveStep

**What it is:** One step in a drone's path. Either the drone is
sitting **at a zone**, or it's **on a link** (transiting to a
restricted zone).

**What it takes (constructor):**

```python
MoveStep(turn: int,
         zone: str | None = None,
         src: str | None = None,
         dst: str | None = None,
         via: tuple[str, str] | None = None)
```

> You never call the constructor directly. Use the class methods:

### Factory methods (how you create MoveSteps)

**1. Zone step — drone is at a zone:**

```python
step = MoveStep.at_zone("roof1", turn=3, via=("hub", "roof1"))
```

| Field | Value | Meaning |
|-------|-------|---------|
| `zone` | "roof1" | The zone the drone is at |
| `turn` | 3 | Which simulation turn |
| `via` | ("hub", "roof1") | The connection used to get here |
| `is_link` | False | This is NOT a link step |
| `label` | "roof1" | For output: `D1-roof1` |

**2. Link step — drone is on a connection (restricted transit):**

```python
step = MoveStep.on_link("hub", "roof1", turn=2)
```

| Field | Value | Meaning |
|-------|-------|---------|
| `src` | "hub" | Where the drone came from |
| `dst` | "roof1" | Where it's going |
| `turn` | 2 | Which simulation turn |
| `is_link` | True | This IS a link step |
| `label` | "hub-roof1" | For output: `D1-hub-roof1` |

### The `via` field — why it exists

When reserving a path, we need to know which **connection** the drone
used to arrive at a zone. Without `via`, the reserve code had to look
**backwards** at the previous step:

```python
# BEFORE (ugly): look at path[i-1]
for i, step in enumerate(path):
    if i > 0:
        prev = path[i - 1]
        if not prev.is_link and prev.zone != step.zone:
            conn = graph.get_connection(prev.zone, step.zone)
            # reserve it...
```

```python
# AFTER (clean): each step knows its own connection
for step in path:
    if step.via:
        conn = graph.get_connection(*step.via)
        # reserve it...
```

Each step is **self-contained**. No looking backwards. No index tracking.
The `via` field makes `_reserve` a simple forward loop.

### Why `__slots__`

```python
__slots__ = ("turn", "_zone", "_src", "_dst", "_via")
```

MoveSteps are created by the **thousands** during search. Each Dijkstra
expansion creates new MoveStep objects. `__slots__` tells Python:
"don't create a `__dict__` for this object — just allocate fixed slots."

Result: ~40% less memory per object. On the challenger map (25 drones,
50+ zones, deep search), thousands of MoveSteps exist simultaneously.

### Properties (read-only access)

| Property | Returns | Notes |
|----------|---------|-------|
| `is_link` | bool | True if `_src is not None` |
| `zone` | str or None | None for link steps |
| `src` | str or None | None for zone steps |
| `dst` | str or None | None for zone steps |
| `via` | tuple or None | (src, dst) of connection used to arrive |
| `label` | str | "zone" or "src-dst" — used for output |

**Why properties instead of public attributes?**

- `_zone`, `_src`, `_dst` are private because a MoveStep is either
  a zone step OR a link step — never both. Properties enforce
  read-only access and make the intent clear.

### `__lt__` and `__eq__`

```python
def __lt__(self, other): return self.turn < other.turn
def __eq__(self, other): return self.turn == other.turn and self.label == other.label
```

`__lt__` is needed for **heap ordering** — Python's `heapq` compares
tuple elements, and if turns are equal, it may compare MoveStep objects.
Without `__lt__`, you get `TypeError: '<' not supported`.

---

## Class: Drone

**What it is:** One drone with an ID, origin, destination, and
assigned path.

**What it takes:**

```python
Drone(drone_id: int, origin: str, destination: str)
```

| Attribute | Type | Set by | Purpose |
|-----------|------|--------|---------|
| `drone_id` | int | constructor | 1, 2, 3, ... |
| `origin` | str | constructor | Start zone name |
| `destination` | str | constructor | End zone name |
| `path` | list[MoveStep] | PathFinder | The planned route |
| `reserved` | bool | PathFinder | True after path is reserved |

**Properties:**

| Property | Returns | How |
|----------|---------|-----|
| `name` | str | `f"D{self.drone_id}"` → "D1", "D2" |
| `last_turn` | int | `self.path[-1].turn` or 0 if no path |

**Why `name` is a property and not stored?**

Because `"D1"` is derived from `drone_id = 1`. Storing it would be
redundant — and if `drone_id` ever changed, the name would be stale.

**Why `reserved` exists?**

It's a flag for debugging and verification. After `PathFinder._reserve()`
runs, it sets `drone.reserved = True`. You can check: if a drone has a
path but `reserved` is False, something went wrong.

**Architecture: why Drone is separate from MoveStep?**

A Drone is an **identity** (who am I, where do I go). A MoveStep is a
**position at a time** (where am I at turn T). They have different
lifecycles:
- MoveSteps are created during search, thrown away if the path is bad
- Drones persist — one per physical drone, assigned once
