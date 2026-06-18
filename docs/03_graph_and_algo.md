# File 3: graph.py + algo.py — GraphNetwork, PathFinder

## Class: GraphNetwork

**What it is:** Undirected graph from hubs and connections.

```python
GraphNetwork(hubs: dict[str, Hub], connections: list[Connection])
```

**State:**
- `self.hubs` — all zones by name
- `self.neighbors` — adjacency list: `{"A": ["B", "C"]}`
- `self.edges` — edge lookup: `{("A","B"): Connection}`

**Edge keys are sorted:** `(min(src,dst), max(src,dst))` so A-B and B-A
find the same Connection.

**`get_neighbor(zone)`** — returns adjacent hubs, skips blocked zones.
Blocked zones return empty list AND are filtered as destinations.

**`get_connection(z1, z2)`** — looks up edge by sorted key. Returns None
if no connection exists.

---

## Class: PathFinder

**What it is:** Core algorithm. Modified Dijkstra with space-time states.

```python
PathFinder(graph: GraphNetwork)
```

**State:**
- `self.can_reach: set[str]` — zones that can reach the goal (reverse DFS)
- `self._max_turn: int` — latest reserved turn (for search limit)

### How the search works

Heap entries: `(turn, cost, priority, zone, path)`
- `turn` = primary sort (fewer turns first)
- `cost` = accumulated priority penalty (tiebreaker)
- `priority` = current zone type priority
- `zone` = current position
- `path` = list of MoveSteps so far

**Loop:** pop lowest turn → if at goal, return → try each neighbor
(capacity check) → try waiting → repeat.

### Capacity checks

- `_zone_free`: start/end always True, others check `hub.is_available(turn)`
- `_link_free`: check `conn.is_available(turn)`
- `_can_move`: normal = check turn+1, restricted = check turn+1 AND turn+2

### Step building

- Normal: `[at_zone(dst, turn+1, via=(src,dst))]`
- Restricted: `[on_link(src, dst, turn+1), at_zone(dst, turn+2)]`

### Reservation

For each step in path:
- Link step → reserve connection at turn AND turn+1
- Zone step → reserve zone at turn, and `step.via` connection at turn

### assign_all_paths

Sequential: find path → reserve → next drone. Greedy approach.
True MAPF is NP-hard. This gives 43 turns on challenger (target: 45).

### Complexity

- Per drone: O(V × T × log(V × T))
- All drones: O(D² × V × log(DV))
- Memory: sparse dicts + __slots__ MoveSteps
