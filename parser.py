"""Read and validate map files."""

from dataclasses import dataclass
from typing import Any


class Hub:
    """One zone on the map."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone: str = "normal",
        max_drones: int = 1,
        color: str = "none",
    ) -> None:
        """Create a hub with position and optional metadata."""
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone: str = zone
        self.max_drones: int = max_drones
        self.color: str = color
        self.reservations: dict[int, int] = {}

    def reserve(self, turn: int) -> None:
        """Reserve one drone slot at this hub for the given turn."""
        self.reservations[turn] = self.reservations.get(turn, 0) + 1

    def usage(self, turn: int) -> int:
        """Return how many drones occupy this hub at a turn."""
        return self.reservations.get(turn, 0)

    def is_reserved(self, turn: int) -> bool:
        """Return True if at least one drone is reserved at this turn."""
        return self.reservations.get(turn, 0) > 0

    def is_available(self, turn: int) -> bool:
        """Return True if this hub has room at the given turn."""
        return self.usage(turn) < self.max_drones


class Connection:
    """A link between two hubs."""

    def __init__(
        self,
        from_hub: str,
        to_hub: str,
        max_link_capacity: int = 1,
    ) -> None:
        """Create a connection with a default capacity of 1."""
        self.from_hub: str = from_hub
        self.to_hub: str = to_hub
        self.max_link_capacity: int = max_link_capacity
        self.reservations: dict[int, int] = {}

    def reserve(self, turn: int) -> None:
        """Reserve one drone slot on this link for the given turn."""
        self.reservations[turn] = self.reservations.get(turn, 0) + 1

    def usage(self, turn: int) -> int:
        """Return how many drones are using this link at the given turn."""
        return self.reservations.get(turn, 0)

    def is_reserved(self, turn: int) -> bool:
        """True if at least one drone uses this link at turn."""
        return self.reservations.get(turn, 0) > 0

    def is_available(self, turn: int) -> bool:
        """Return True if this link has room at the given turn."""
        return self.usage(turn) < self.max_link_capacity


@dataclass
class MapData:
    """Contains all parsed data from a map file."""

    nb_drones: int
    start_hub: Hub
    end_hub: Hub
    hubs: dict[str, Hub]
    connections: list[Connection]


class Parser:
    """Parse nb_drones, hubs, and connections from a map file."""

    VALID_ZONES = ("normal", "blocked", "restricted", "priority")

    def __init__(self) -> None:
        """Prepare empty parser state."""
        self.nb_drones: int = 0
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None
        self.hubs: dict[str, Hub] = {}
        self.connections: list[Connection] = []
        self.seen_connections: set[str] = set()

    def open_file(self, file: str) -> list[str]:
        """Read all lines from a map file."""
        with open(file, "r") as f:
            return f.readlines()

    def parse_nb_drone(self, line: str, i: int) -> None:
        """Read the nb_drones value from one line."""
        # handle nb drone li moraha
        try:
            t = line.split(":")
            if len(t) != 2:
                raise ValueError(
                    f"Line {i}: Has duplicate ':'"
                )
            value = t[1].strip()
        except IndexError:
            raise ValueError(f"Line {i}: Missing ':' delimiter or value")

        if not value:
            raise ValueError(f"Line {i}: nb_drones is empty")

        try:
            nb = int(value)
        except ValueError:
            raise ValueError(f"Line {i}: nb_drones must be an integer")

        if nb <= 0:
            raise ValueError(f"Line {i}: nb_drones must be positive")

        self.nb_drones = nb

    def _parse_metadata(self, attr: str, i: int) -> dict[str, Any]:
        """Parse hub metadata inside [brackets]."""
        zone: str | None = None
        color: str | None = None
        max_drones: int | None = None

        if not attr:
            return {"zone": "normal", "color": "none", "max_drones": 1}

        for part in attr.split():
            if "=" not in part:
                raise ValueError(
                    f"Line {i}: Invalid metadata token '{part}'"
                )

            key, val = part.split("=", 1)
            if key == "max_drones":
                if max_drones is not None:
                    raise ValueError(
                        f"Line {i}: Duplicate max_drones"
                    )
                try:
                    nb = int(val)
                    if nb <= 0:
                        raise ValueError()
                    max_drones = nb
                except ValueError:
                    raise ValueError(
                        f"Line {i}: max_drones must be positive"
                    )
            elif key == "zone":
                if zone is not None:
                    raise ValueError(f"Line {i}: Duplicate zone parameter")
                if val not in self.VALID_ZONES:
                    raise ValueError(
                        f"Line {i}: Invalid zone type '{val}'"
                    )
                zone = val
            elif key == "color":
                if color is not None:
                    raise ValueError(
                        f"Line {i}: Duplicate color"
                    )

                if (
                    not val
                    or val.lower() == "none"
                    or "=" in val
                    or len(val.split()) > 1
                ):
                    raise ValueError(
                        f"Line {i}: Color must be a"
                        f" single non-empty word"
                    )
                color = val
            else:
                raise ValueError(
                    f"Line {i}: Unknown metadata key '{key}'"
                )

        return {
            "zone": zone if zone is not None else "normal",
            "color": color if color is not None else "none",
            "max_drones": max_drones if max_drones is not None else 1,
        }

    def _extract_brackets(
        self, data: str, i: int
    ) -> tuple[str, str]:
        """Split data into content before brackets and metadata."""
        open_b = data.find("[")
        close_b = data.find("]")

        if open_b == -1 and close_b == -1:
            return data, ""
        if open_b != -1 and close_b == -1:
            raise ValueError(
                f"Line {i}: Unclosed '[' in metadata"
            )
        if open_b == -1 and close_b != -1:
            raise ValueError(
                f"Line {i}: Unexpected ']' without opening '['"
            )
        if close_b < open_b:
            raise ValueError(
                f"Line {i}: ']' appears before '['"
            )

        attr = data[open_b + 1:close_b].strip()

        trailing = data[close_b + 1:].strip()
        if trailing:
            raise ValueError(
                f"Line {i}: Unexpected text after ']'"
            )

        body = data[:open_b].strip()
        return body, attr

    def hub_parse(self, data: str, i: int) -> Hub:
        """Parse one hub line into a Hub object."""
        data, attr = self._extract_brackets(data, i)

        parts = data.split()
        if len(parts) < 3:
            raise ValueError(
                f"Line {i}: Hub missing name, x, y parameters"
            )
        if len(parts) > 3:
            raise ValueError(
                f"Line {i}: Unexpected tokens after x, y"
            )

        name = parts[0]
        if "-" in name or " " in name:
            raise ValueError(
                f"Line {i}: Zone name '{name}' contains invalid "
                f"characters (no dashes or spaces allowed)"
            )

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            raise ValueError(f"Line {i}: x and y must be integers")
        meta = self._parse_metadata(attr, i)
        return Hub(name=name, x=x, y=y, **meta)

    def connection_parsing(self, data: str, i: int) -> Connection:
        """Parse one connection line into a Connection object."""
        data, attr = self._extract_brackets(data, i)
        cap = 1
        max_link_seen = False

        parts = data.split("-")
        if len(parts) != 2:
            raise ValueError(
                f"Line {i}: Connection must be 'from-to'"
            )

        from_hub = parts[0].strip()
        to_hub = parts[1].strip()
        if not from_hub or not to_hub:
            raise ValueError(
                f"Line {i}: Connection names cannot be empty"
            )

        if from_hub == to_hub:
            raise ValueError(
                f"Line {i}: Self-connection '{from_hub}-{to_hub}'"
            )

        if from_hub not in self.hubs:
            raise ValueError(
                f"Line {i}: Connection source '{from_hub}' undefined"
            )
        if to_hub not in self.hubs:
            raise ValueError(
                f"Line {i}: Connection target '{to_hub}' undefined"
            )

        key = "-".join(sorted([from_hub, to_hub]))
        if key in self.seen_connections:
            raise ValueError(
                f"Line {i}: Duplicate connection '{from_hub}-{to_hub}'"
            )
        self.seen_connections.add(key)

        if attr:
            for part in attr.split():
                if "=" not in part:
                    raise ValueError(
                        f"Line {i}: Invalid metadata token '{part}'"
                    )
                k, v = part.split("=", 1)
                if k == "max_link_capacity":
                    if max_link_seen:
                        raise ValueError(
                            f"Line {i}: Duplicate"
                            f" max_link_capacity"
                        )
                    max_link_seen = True
                    try:
                        nb = int(v)
                        if nb <= 0:
                            raise ValueError()
                        cap = nb
                    except ValueError:
                        raise ValueError(
                            f"Line {i}: max_link_capacity must be positive"
                        )
                else:
                    raise ValueError(
                        f"Line {i}: Unknown metadata key '{k}'"
                    )

        return Connection(from_hub, to_hub, cap)

    def starter_parsing(self, file: str) -> MapData:
        """Read the whole map file and fill parser fields."""
        lines = self.open_file(file)
        line_num = 1
        got_drones = False

        for raw_line in lines:
            line = raw_line.strip().split("#", 1)[0]
            if not line or line.startswith("#"):
                line_num += 1
                continue

            if not line:
                line_num += 1
                continue

            if not got_drones:
                if not line.startswith("nb_drones:"):
                    raise ValueError(
                        f"Line {line_num}: Expected 'nb_drones:' first"
                    )
                self.parse_nb_drone(line, line_num)
                got_drones = True
                line_num += 1
                continue

            if ":" not in line:
                raise ValueError(f"Line {line_num}: Expected \':\' separator")

            prefix, data = line.split(":", 1)
            prefix = prefix.strip()
            data = data.strip()

            if prefix in ("start_hub", "end_hub", "hub"):
                hub = self.hub_parse(data, line_num)
                if hub.name in self.hubs:
                    raise ValueError(
                        f"Line {line_num}: Hub '{hub.name}' already exists"
                    )
                self.hubs[hub.name] = hub

                if prefix == "start_hub":
                    if self.start_hub is not None:
                        raise ValueError(
                            f"Line {line_num}: Duplicate start_hub"
                        )
                    self.start_hub = hub
                elif prefix == "end_hub":
                    if self.end_hub is not None:
                        raise ValueError(
                            f"Line {line_num}: Duplicate end_hub"
                        )
                    self.end_hub = hub

            elif prefix == "connection":
                self.connections.append(
                    self.connection_parsing(data, line_num)
                )
            elif prefix == "nb_drones":
                raise ValueError(
                    f"Line {line_num}: Duplicate nb_drones definition"
                )
            else:
                raise ValueError(
                    f"Line {line_num}: Unknown prefix '{prefix}'"
                )

            line_num += 1

        if not got_drones:
            raise ValueError("Missing nb_drones definition")
        if self.start_hub is None:
            raise ValueError("Missing start_hub")
        if self.end_hub is None:
            raise ValueError("Missing end_hub")

        hub_list = list(self.hubs.values())
        for idx_a in range(len(hub_list)):
            for idx_b in range(idx_a + 1, len(hub_list)):
                hub_a = hub_list[idx_a]
                hub_b = hub_list[idx_b]
                if hub_a.x == hub_b.x and hub_a.y == hub_b.y:
                    raise ValueError(
                        f"Coordinate Conflict Error:"
                        f" Hub '{hub_a.name}' and"
                        f" Hub '{hub_b.name}' share"
                        f" position"
                        f" ({hub_a.x}, {hub_a.y})."
                    )

        return MapData(
            nb_drones=self.nb_drones,
            start_hub=self.start_hub,
            end_hub=self.end_hub,
            hubs=self.hubs,
            connections=self.connections,
        )
