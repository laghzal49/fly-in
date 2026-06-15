# `reservation.py`

## Purpose

`reservation.py` stores how many drones use each zone or link at each turn.

`PathFinder` uses it to avoid collisions while routing drones one by one.

---

## Class

```python
ReservationTable
```

Internal storage:

```python
table: dict[tuple[str, int], int]
```

Key format:

| Key          | Meaning                        |
| ------------ | ------------------------------ |
| `("A", 3)`   | drones in zone `A` at turn 3   |
| `("A_B", 4)` | drones on link `A-B` at turn 4 |

Link names are sorted internally, so `A-B` and `B-A` use the same key.

---

## Methods

### `reserve_zone(zone, turn)`

Adds one drone to a zone at a turn.

### `is_zone_available(zone, turn, capacity)`

Returns `True` if:

```python
current_count < capacity
```

### `reserve_link(z1, z2, turn)`

Adds one drone to a link at a turn.

### `is_link_available(z1, z2, turn, capacity)`

Same as zones, but for links.

---

## Example

```python
table.reserve_zone("gate", 2)
table.is_zone_available("gate", 2, 1)  # False
```

The zone is full because one drone already reserved it and capacity is `1`.

---

## Used by

- `main.py` creates the table
- `algo.py` reads and writes reservations
