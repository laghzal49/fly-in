# parser.py

## Purpose

Reads and validates the map file format. Turns text lines into `Hub` and
`Connection` objects that the rest of the program uses.

## Location in the pipeline

```
map.txt  →  Parser  →  hubs dict + connections list + nb_drones
```

## Classes

### `Hub`

Represents one zone on the map.

| Field | Default | Meaning |
|-------|---------|---------|
| `name` | required | Unique zone name (no `-` or spaces) |
| `x`, `y` | required | Integer coordinates (stored, not used for routing) |
| `zone` | `"normal"` | Type: normal, blocked, restricted, priority |
| `max_drones` | `1` | Max drones in zone at same turn |
| `color` | `"none"` | Terminal color name for simulation |

### `Connection`

Bidirectional link between two hubs.

| Field | Default | Meaning |
|-------|---------|---------|
| `from_hub`, `to_hub` | required | Hub names (must exist) |
| `max_link_capacity` | `1` | Max drones on link at same turn |

### `Parser`

Main parser class. Public fields after parsing:

| Field | Type | Content |
|-------|------|---------|
| `nb_drones` | `int` | Fleet size |
| `start_hub` | `Hub` | Starting zone |
| `end_hub` | `Hub` | Goal zone |
| `hubs` | `dict[str, Hub]` | All zones by name |
| `connections` | `list[Connection]` | All links |

## Methods

| Method | Visibility | Role |
|--------|------------|------|
| `open_file(file)` | public | Read file lines; raise on missing file |
| `parse_nb_drone(line, i)` | public | Parse `nb_drones: N` |
| `hub_parse(data, i)` | public | Parse one hub line |
| `connection_parsing(data, i)` | public | Parse one connection line |
| `starter_parsing(file)` | public | Main loop over all lines |
| `_parse_metadata(attr, i)` | private | Parse `[zone=... color=...]` |

## How `starter_parsing` works

```mermaid
flowchart TD
    A[Read each line] --> B{Comment or empty?}
    B -->|yes| A
    B -->|no| C{First line?}
    C -->|yes| D[Must be nb_drones:]
    C -->|no| E{prefix:}
    E -->|start_hub/end_hub/hub| F[hub_parse → hubs dict]
    E -->|connection| G[connection_parsing → list]
    E -->|other| H[Error]
    F --> A
    G --> A
    D --> A
```

Rules enforced:
- First real line must be `nb_drones:`
- Exactly one `start_hub` and one `end_hub`
- No duplicate hub names or connections
- Connections only between existing hubs
- Invalid metadata → `ValueError` with line number

## Example input

```
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: hello 1 0 [color=blue]
end_hub: goal 3 0 [color=red]
connection: start-hello
connection: hello-goal
```

## Example output (parser state)

```python
parser.nb_drones == 2
parser.start_hub.name == "start"
parser.end_hub.name == "goal"
len(parser.hubs) == 3
len(parser.connections) == 2
```

## Error handling

Parser prints `Fatal Error: ...` to stderr and calls `sys.exit(1)` on:
- Bad line format
- Missing start/end hub after parsing
- Duplicate definitions

## Dependencies

- Standard library only: `sys`, `typing`
- No imports from other project files

## Used by

- `main.py` — creates `Parser`, calls `starter_parsing`
- `graph.py` — receives `Hub` and `Connection` objects
- `simulation.py` — uses `Hub` for colors
