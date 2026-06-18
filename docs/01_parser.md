# File 1: parser.py — Hub, Connection, MapData, Parser

## Overview

`parser.py` reads a map file and produces structured data objects.
It contains **4 classes**: Hub, Connection, MapData, and Parser.

---

## Class: Hub

**What it is:** One zone on the map.

**What it takes (constructor):**

```python
Hub(name: str, x: int, y: int,
    zone: str = "normal",
    max_drones: int = 1,
    color: str = "none")
```

| Param | Type | Default | Why |
|-------|------|---------|-----|
| `name` | str | required | Unique identifier like "roof1" |
| `x, y` | int | required | Coordinates (for visualization) |
| `zone` | str | "normal" | One of: normal, blocked, restricted, priority |
| `max_drones` | int | 1 | How many drones can be here at once |
| `color` | str | "none" | ANSI color for terminal output |

**Internal state:**

```python
self.reservations: dict[int, int] = {}
# Example: {0: 1, 1: 2, 3: 1}
# Meaning: 1 drone at turn 0, 2 drones at turn 1, 1 drone at turn 3
```

**Methods:**

| Method | Signature | What it does | Example |
|--------|-----------|-------------|---------|
| `reserve` | `(turn: int) -> None` | Adds 1 drone at this turn | `hub.reserve(5)` → `{5: 1}` → `{5: 2}` |
| `usage` | `(turn: int) -> int` | Count of drones at turn | `hub.usage(5)` → `2` |
| `is_reserved` | `(turn: int) -> bool` | Any drone here? | `hub.is_reserved(5)` → `True` |
| `is_available` | `(turn: int) -> bool` | Room for one more? | `hub.is_available(5)` with max_drones=3 → `True` |

**Why Hub tracks its own reservations:**

Before, we had a separate `ReservationTable` class. The Hub didn't know
its own state — the table stored `{("roof1", 5): 2}` separately.
Problem: two data structures to keep in sync, string-based lookups.

Now: `hub.reserve(5)` and `hub.is_available(5)` are right on the object.
Hub knows its own capacity (`max_drones`) and its own usage. Nobody
else needs to compare them — `is_available()` does it internally.

**How `is_available` works:**

```python
def is_available(self, turn: int) -> bool:
    return self.usage(turn) < self.max_drones
```

Simple: if current usage is less than max, there's room.

---

## Class: Connection

**What it is:** A link between two hubs.

**What it takes:**

```python
Connection(from_hub: str, to_hub: str,
           max_link_capacity: int = 1)
```

**Identical pattern to Hub** — same 4 methods:
`reserve`, `usage`, `is_reserved`, `is_available`.

Only difference: `max_link_capacity` instead of `max_drones`.

**Why same pattern?** Both zones and links answer the same question:
"how many drones are using me at turn T?" The logic is identical,
just with different capacity limits.

---

## Class: MapData

**What it is:** A `@dataclass` that bundles all parsed data.

```python
@dataclass
class MapData:
    nb_drones: int             # how many drones to route
    start_hub: Hub             # the starting zone
    end_hub: Hub               # the destination zone
    hubs: dict[str, Hub]       # all zones by name
    connections: list[Connection]  # all links
```

**Why a dataclass?** It's just a container — no methods, no logic.
`@dataclass` auto-generates `__init__`, `__repr__`, etc. Clean and
minimal.

---

## Class: Parser

**What it is:** Reads a map file line by line, validates everything,
returns a `MapData`.

**What it takes:**

```python
Parser()  # no arguments — state is built during parsing
```

**Internal state:**

```python
self.nb_drones: int = 0
self.start_hub: Optional[Hub] = None
self.end_hub: Optional[Hub] = None
self.hubs: dict[str, Hub] = {}
self.connections: list[Connection] = []
self.seen_connections: set[str] = set()  # for duplicate detection
```

**Key methods:**

| Method | What it does |
|--------|-------------|
| `open_file(path)` | Reads all lines with `with open()` (context manager) |
| `parse_nb_drone(line, i)` | Validates and extracts drone count |
| `parse_zone_metadata(attr, i)` | Parses `[zone=restricted color=red max_drones=2]` |
| `parse_hub(line, i, kind)` | Parses one hub line (start_hub/end_hub/hub) |
| `parse_connection(line, i)` | Parses `connection: A-B [max_link_capacity=2]` |
| `starter_parsing(file)` | Main entry: reads file → validates → returns MapData |

**Validation rules (from the subject):**

1. First non-comment line must be `nb_drones: N` (positive integer)
2. Exactly one `start_hub:` and one `end_hub:`
3. Zone names: no dashes (because connections use `A-B` format)
4. Zone names: no spaces, must be unique
5. No duplicate connections (`A-B` = `B-A`)
6. Zone types must be: normal, blocked, restricted, priority
7. `max_drones` and `max_link_capacity` must be positive integers
8. Every error includes line number: `"Line 5: Duplicate color"`

**Why `seen_connections` uses a sorted key?**

```python
key = f"{min(a, b)}-{max(a, b)}"
```

Because `A-B` and `B-A` are the same connection. Sorting ensures
one canonical form for duplicate detection.

**Architecture decision: why Parser is its own class?**

Parsing rules change independently from routing logic. If the
map format changes (new metadata fields, new zone types), only
`parser.py` changes. The rest of the codebase doesn't care how
the data was read — it just receives Hub, Connection, MapData objects.
