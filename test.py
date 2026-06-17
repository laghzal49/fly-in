fake_connections = {
    "A": [("B", 1), ("C", 1)],
    "B": [("C", 1), ("D", 1)],
    "C": [("D", 1), ("E", 1)],
    "D": [("E", 1), ("F", 1), ("G", 1)],
    "E": [("C", 1), ("D", 1), ("F", 1), ("G", 1)],
    "F": [("D", 1), ("E", 1), ("G", 1), ("H", 1)],
    "G": [("D", 1), ("E", 1), ("F", 1), ("H", 1), ("I", 1)],
    "H": [("F", 1), ("G", 1), ("I", 1), ("J", 1)],
    "I": [("G", 1), ("H", 1), ("J", 1), ("K", 1)],
    "J": [("H", 1), ("I", 1), ("K", 1), ("L", 1)],
    "K": [("I", 1), ("J", 1), ("L", 1), ("M", 1)],
    "L": [("J", 1), ("K", 1), ("M", 1), ("N", 1)],
}



import heapq


def algorithm(start, end):
    heap: list[int, str, list[str, int]] = [(0, start, [(start, 0)])]
    seen: set[tuple[str, int]] = set()
    while heap:
        turn, zone, path = heapq.heappop(heap)
        if zone == end:
            return path
        state = (zone, turn)
        if state in seen:
            continue
        seen.add(state)
        for neighbor, cost in fake_connections.get(zone, []):
            max_turn = max(turn for _, turn in seen) + 10
            if turn + 1 >= max_turn:
                return []
            next_turn = turn + cost
            if (neighbor, next_turn) in seen:
                continue
            heapq.heappush(
                heap,
                (next_turn, neighbor, path + [(neighbor, next_turn)]),
            )
    return []


print(f"Path from F to G: {algorithm('B', 'A') if algorithm('B', 'A') else 'No path'}")
