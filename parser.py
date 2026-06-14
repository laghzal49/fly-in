"""Read and validate map files."""

import sys
from typing import Any, Dict, List, Optional


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
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.max_drones = max_drones
        self.color = color


class Connection:
    """A link between two hubs."""

    def __init__(
        self,
        from_hub: str,
        to_hub: str,
        max_link_capacity: int = 1,
    ) -> None:
        """Create a connection with a default capacity of 1."""
        self.from_hub = from_hub
        self.to_hub = to_hub
        self.max_link_capacity = max_link_capacity


class Parser:
    """Parse nb_drones, hubs, and connections from a map file."""

    VALID_ZONES = ("normal", "blocked", "restricted", "priority")

    def __init__(self) -> None:
        """Prepare empty parser state."""
        self.nb_drones = 0
        self.start_hub: Optional[Hub] = None
        self.end_hub: Optional[Hub] = None
        self.hubs: Dict[str, Hub] = {}
        self.connections: List[Connection] = []
        self.seen_connections: set[str] = set()

    def open_file(self, file: str) -> List[str]:
        """Read all lines from a map file."""
        try:
            with open(file, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file} not found.")
        except Exception as e:
            raise Exception(f"Error opening file: {e}")

    def parse_nb_drone(self, line: str, i: int) -> None:
        """Read the nb_drones value from one line."""
        try:
            value = line.split(":")[1].strip()
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

    def _parse_metadata(self, attr: str, i: int) -> Dict[str, Any]:
        """Parse hub metadata inside [brackets]."""
        data: Dict[str, Any] = {
            "zone": "normal",
            "color": "none",
            "max_drones": 1,
        }
        if not attr:
            return data

        for part in attr.split():
            if "=" not in part:
                raise ValueError(
                    f"Line {i}: Invalid metadata token '{part}'"
                )

            key, val = part.split("=", 1)
            if key == "max_drones":
                try:
                    nb = int(val)
                    if nb <= 0:
                        raise ValueError()
                    data[key] = nb
                except ValueError:
                    raise ValueError(
                        f"Line {i}: max_drones must be positive"
                    )
            elif key == "zone":
                if val not in self.VALID_ZONES:
                    raise ValueError(
                        f"Line {i}: Invalid zone type '{val}'"
                    )
                data[key] = val
            elif key == "color":
                data[key] = val
            else:
                raise ValueError(
                    f"Line {i}: Unknown metadata key '{key}'"
                )

        return data

    def hub_parse(self, data: str, i: int) -> Hub:
        """Parse one hub line into a Hub object."""
        attr = ""
        start = data.find("[")
        end = data.find("]")

        if start != -1 and end != -1 and end > start:
            attr = data[start + 1:end]
            data = data[:start].strip()

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
        attr = ""
        cap = 1
        start = data.find("[")
        end = data.find("]")

        if start != -1 and end != -1 and end > start:
            attr = data[start + 1:end]
            data = data[:start].strip()

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
                f"Line {i}: Duplicate connection "
                f"'{from_hub}-{to_hub}'"
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
                    try:
                        nb = int(v)
                        if nb <= 0:
                            raise ValueError()
                        cap = nb
                    except ValueError:
                        raise ValueError(
                            f"Line {i}: max_link_capacity must be "
                            f"positive"
                        )
                else:
                    raise ValueError(
                        f"Line {i}: Unknown metadata key '{k}'"
                    )

        return Connection(from_hub, to_hub, cap)

    def starter_parsing(self, file: str) -> None:
        """Read the whole map file and fill parser fields."""
        lines = self.open_file(file)
        line_num = 1
        got_drones = False

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                line_num += 1
                continue

            if not got_drones:
                if not line.startswith("nb_drones:"):
                    raise ValueError(
                        f"Line {line_num}: Expected 'nb_drones:' first"
                    )
                try:
                    self.parse_nb_drone(line, line_num)
                    got_drones = True
                except ValueError as e:
                    print(f"Fatal Error: {e}", file=sys.stderr)
                    sys.exit(1)
                line_num += 1
                continue

            if ":" not in line:
                print(
                    f"Fatal Error (Line {line_num}): "
                    f"Expected ':' separator",
                    file=sys.stderr,
                )
                sys.exit(1)

            prefix, data = line.split(":", 1)
            prefix = prefix.strip()
            data = data.strip()

            try:
                if prefix in ("start_hub", "end_hub", "hub"):
                    hub = self.hub_parse(data, line_num)
                    if hub.name in self.hubs:
                        raise ValueError(
                            f"Line {line_num}: Hub "
                            f"'{hub.name}' already exists"
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
                        f"Line {line_num}: Duplicate nb_drones "
                        f"definition"
                    )
                else:
                    raise ValueError(
                        f"Line {line_num}: Unknown prefix '{prefix}'"
                    )
            except ValueError as e:
                print(f"Fatal Error: {e}", file=sys.stderr)
                sys.exit(1)

            line_num += 1

        if self.start_hub is None:
            print("Fatal Error: Missing start_hub", file=sys.stderr)
            sys.exit(1)
        if self.end_hub is None:
            print("Fatal Error: Missing end_hub", file=sys.stderr)
            sys.exit(1)
