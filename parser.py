import sys
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


class Hub:
    """
    Represents a hub in the network with its properties and location.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone: str = "normal",
        max_drones: int = 1,
        color: str = "none",
    ) -> None:
        """
        Initializes a Hub with name, coordinates, and optional properties.
        """
        self.name = name
        self.x = x
        self.y = y
        self.zone = zone
        self.max_drones = max_drones
        self.color = color
        self.priority_weight = {
            "priority": 1, "normal": 1, "restricted": 2, "blocked": 9999
        }.get(zone, 1)


@dataclass
class Connection:
    """
    Represents a connection between two hubs with a capacity.
    """
    from_hub: str
    to_hub: str
    max_link_capacity: int = 1


class Parser:
    """
    Parses map files to extract hubs, connections, and simulation parameters.
    """
    VALID_ZONES = ("normal", "blocked", "restricted", "priority")

    def __init__(self) -> None:
        """
        Initializes the Parser with empty data structures.
        """
        self.nb_drones: int = 0
        self.start_hub: Optional[Hub] = None
        self.end_hub: Optional[Hub] = None
        self.hubs: Dict[str, Hub] = {}
        self.connections: List[Connection] = []
        self.seen_connections: set[str] = set()

    def open_file(self, file: str) -> List[str]:
        """
        Opens and reads all lines from a file.
        """
        try:
            with open(file, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file} not found.")
        except Exception as e:
            raise Exception(f"Error opening file: {e}")

    def parse_nb_drone(self, line: str, i: int) -> None:
        """
        Parses the number of drones from a line.
        """
        try:
            value = line.split(":")[1].strip()
        except IndexError:
            raise ValueError(
                f"Line {i}: Missing ':' delimiter or value"
            )
        if not value:
            raise ValueError(f"Line {i}: nb_drones is empty")
        try:
            nb = int(value)
        except ValueError:
            raise ValueError(
                f"Line {i}: nb_drones must be an integer"
            )
        if nb <= 0:
            raise ValueError(
                f"Line {i}: nb_drones must be positive"
            )
        self.nb_drones = nb

    def _parse_metadata(self, attr: str, i: int) -> Dict[str, Any]:
        """
        Parse metadata from attribute string.
        """
        kwargs: Dict[str, Any] = {
            "zone": "normal", "color": "none", "max_drones": 1
        }
        if not attr:
            return kwargs

        for element in attr.split():
            if "=" not in element:
                raise ValueError(
                    f"Line {i}: Invalid metadata token '{element}'"
                )
            k, v = element.split("=", 1)

            if k == "max_drones":
                try:
                    val = int(v)
                    if val <= 0:
                        raise ValueError()
                    kwargs[k] = val
                except ValueError:
                    raise ValueError(
                        f"Line {i}: max_drones must be positive"
                    )
            elif k == "zone":
                if v not in self.VALID_ZONES:
                    raise ValueError(
                        f"Line {i}: Invalid zone type '{v}'"
                    )
                kwargs[k] = v
            elif k == "color":
                kwargs[k] = v
            else:
                raise ValueError(f"Line {i}: Unknown metadata key '{k}'")

        return kwargs

    def hub_parse(self, data: str, i: int) -> Hub:
        """
        Parses a hub definition from a data string.
        """
        meta_start = data.find("[")
        meta_end = data.find("]")
        attr = ""

        if meta_start != -1 and meta_end != -1 and meta_end > meta_start:
            attr = data[meta_start + 1:meta_end]
            data = data[:meta_start].strip()

        parts = data.split()
        if len(parts) < 3:
            raise ValueError(
                f"Line {i}: Hub missing name, x, y parameters"
            )
        if len(parts) > 3:
            raise ValueError(
                f"Line {i}: Unexpected tokens after x, y")
        name = parts[0]
        if "-" in name:
            raise ValueError(
                f"Line {i}: Zone name '{name}' contains dashes"
            )

        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Line {i}: x and y must be integers")

        kwargs = self._parse_metadata(attr, i)
        return Hub(name=name, x=x, y=y, **kwargs)

    def connection_parsing(self, data: str, i: int) -> Connection:
        """
        Parses a connection definition from a data string.
        """
        meta_start = data.find("[")
        meta_end = data.find("]")
        attr = ""
        max_link_capacity = 1

        if meta_start != -1 and meta_end != -1 and meta_end > meta_start:
            attr = data[meta_start + 1:meta_end]
            data = data[:meta_start].strip()

        parts = data.split("-")
        if len(parts) != 2:
            raise ValueError(
                f"Line {i}: Connection must be 'from-to'"
            )

        from_hub, to_hub = parts[0].strip(), parts[1].strip()
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

        fingerprint = "-".join(sorted([from_hub, to_hub]))
        if fingerprint in self.seen_connections:
            raise ValueError(
                f"Line {i}: Duplicate connection '{from_hub}-{to_hub}'"
            )
        self.seen_connections.add(fingerprint)

        if attr:
            for element in attr.split():
                if "=" not in element:
                    raise ValueError(
                        f"Line {i}: Invalid metadata token '{element}'"
                    )
                k, v = element.split("=", 1)
                if k == "max_link_capacity":
                    try:
                        val = int(v)
                        if val <= 0:
                            raise ValueError()
                        max_link_capacity = val
                    except ValueError:
                        raise ValueError(
                            f"Line {i}: max_link_capacity must be positive"
                        )
                else:
                    raise ValueError(f"Line {i}: Unknown metadata key '{k}'")
        return Connection(
            from_hub=from_hub,
            to_hub=to_hub,
            max_link_capacity=max_link_capacity,
        )

    def starter_parsing(self, file: str) -> None:
        """
        Main parsing loop that orchestrates the map file processing.
        """
        lines = self.open_file(file)
        i = 1
        has_parsed_drones = False

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"):
                i += 1
                continue

            if not has_parsed_drones:
                if not line.startswith("nb_drones:"):
                    raise ValueError(
                        f"Line {i}: Expected 'nb_drones:' first"
                    )
                try:
                    self.parse_nb_drone(line, i)
                    has_parsed_drones = True
                except ValueError as e:
                    print(f"Fatal Error: {e}", file=sys.stderr)
                    sys.exit(1)
                i += 1
                continue

            if ":" not in line:
                print(
                    f"Fatal Error (Line {i}): Expected ':' separator",
                    file=sys.stderr
                )
                sys.exit(1)

            prefix, data = line.split(":", 1)
            prefix = prefix.strip()
            data = data.strip()

            try:
                if prefix in ("start_hub", "end_hub", "hub"):
                    hub = self.hub_parse(data, i)
                    if hub.name in self.hubs:
                        raise ValueError(
                            f"Line {i}: Hub '{hub.name}' already exists"
                        )
                    self.hubs[hub.name] = hub

                    if prefix == "start_hub":
                        if self.start_hub is not None:
                            raise ValueError(
                                f"Line {i}: Duplicate start_hub"
                            )
                        self.start_hub = hub
                    elif prefix == "end_hub":
                        if self.end_hub is not None:
                            raise ValueError(
                                f"Line {i}: Duplicate end_hub"
                            )
                        self.end_hub = hub

                elif prefix == "connection":
                    self.connections.append(
                        self.connection_parsing(data, i)
                    )
                elif prefix == "nb_drones":
                    raise ValueError(
                        f"Line {i}: Duplicate nb_drones definition"
                    )
                else:
                    raise ValueError(
                        f"Line {i}: Unknown prefix '{prefix}'"
                    )

            except ValueError as e:
                print(f"Fatal Error: {e}", file=sys.stderr)
                sys.exit(1)

            i += 1

        if self.start_hub is None:
            print("Fatal Error: Missing start_hub", file=sys.stderr)
            sys.exit(1)
        if self.end_hub is None:
            print("Fatal Error: Missing end_hub", file=sys.stderr)
            sys.exit(1)
