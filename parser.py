import sys
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class Hub:
    name: str
    x: int
    y: int
    zone: str = "normal"
    color: str = "none"
    max_drones: int = 1


@dataclass
class Connection:
    from_hub: str
    to_hub: str
    max_link_capacity: int = 1


class Parser:
    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hubs: Dict[str, Hub] = {}
        self.connections: List[Connection] = []
        self.seen_connections = set()
        self.errors: List[str] = []

    def open_file(self, file: str):
        try:
            with open(file, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file} not found.")
        except Exception as e:
            raise Exception(f"An error occurred while opening the file: {e}")

    def parse_nb_drone(self, line: str, i: int):
        try:
            value = line.split(":")[1].strip()
        except IndexError:
            raise ValueError(
                f"Line {i}: Missing ':' delimiter or value entirely"
            )
        if not value:
            raise ValueError(f"Line {i}: nb_drones should not be empty")
        try:
            nb = int(value)
        except ValueError:
            raise ValueError(
                f"Line {i}: Number of Drone Should be a valid integer"
            )

        if nb <= 0:
            raise ValueError(
                f"Line {i}: Number of Drone should be a positive integer > 0"
            )
        self.nb_drones = nb

    def hub_parse(self, data: str, i: int) -> Hub:
        meta_start = data.find("[")
        meta_end = data.find("]")
        attr = ""
        kwargs: Dict[str, Any] = {
            "zone": "normal",
            "color": "none",
            "max_drones": 1
        }

        if meta_start != -1 and meta_end != -1 and meta_end > meta_start:
            attr = data[meta_start + 1: meta_end]
            data = data[:meta_start].strip()

        parts = data.split()
        if len(parts) < 3:
            raise ValueError(
                f"Line {i}: Hub is missing basic parameters (name, x, y)"
            )

        name = parts[0]

        if '-' in name:
            raise ValueError(
                f"Line {i}: Zone name '{name}' is invalid. Dashes forbidden."
            )

        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            raise ValueError(f"Line {i}: x and y need to be integer")

        if attr:
            for element in attr.split():
                if '=' not in element:
                    raise ValueError(
                        f"Line {i}: Invalid metadata token '{element}'"
                    )
                k, v = element.split('=', 1)

                if k == "max_drones":
                    try:
                        val = int(v)
                        if val <= 0:
                            raise ValueError()
                        kwargs[k] = val
                    except ValueError:
                        raise ValueError(
                            f"Line {i}: max_drones must be a positive integer"
                        )
                elif k == "zone":
                    if v not in ("normal", "blocked", "restricted", "priority"):
                        raise ValueError(
                            f"Line {i}: Invalid zone type '{v}'. Must be: "
                            "normal, blocked, restricted, priority"
                        )
                    kwargs[k] = v
                elif k == "color":
                    kwargs[k] = v

        return Hub(name=name, x=x, y=y, **kwargs)

    def connection_parsing(self, data: str, i: int) -> Connection:
        meta_start = data.find("[")
        meta_end = data.find("]")
        attr = ""
        max_link_capacity = 1

        if meta_start != -1 and meta_end != -1 and meta_end > meta_start:
            attr = data[meta_start + 1: meta_end]
            data = data[:meta_start].strip()

        node = data.split('-')
        if len(node) != 2:
            raise ValueError(
                f"Line {i}: Connection format must match 'from_hub-to_hub'"
            )

        from_hub = node[0].strip()
        to_hub = node[1].strip()

        if not from_hub or not to_hub:
            raise ValueError(
                f"Line {i}: Connection source/target name cannot be blank"
            )

        if from_hub not in self.hubs:
            raise ValueError(
                f"Line {i}: Connection source '{from_hub}' is undefined."
            )
        if to_hub not in self.hubs:
            raise ValueError(
                f"Line {i}: Connection target '{to_hub}' is undefined."
            )

        fingerprint = "-".join(sorted([from_hub, to_hub]))
        if fingerprint in self.seen_connections:
            raise ValueError(
                f"Line {i}: Duplicate connection detected for "
                f"'{from_hub}' and '{to_hub}'."
            )
        self.seen_connections.add(fingerprint)

        if attr:
            for element in attr.split():
                if '=' not in element:
                    raise ValueError(
                        f"Line {i}: Invalid metadata token '{element}'"
                    )
                k, v = element.split('=', 1)
                if k == "max_link_capacity":
                    try:
                        val = int(v)
                        if val <= 0:
                            raise ValueError()
                        max_link_capacity = val
                    except ValueError:
                        raise ValueError(
                            f"Line {i}: max_link_capacity must be a "
                            "positive integer"
                        )

        return Connection(
            from_hub=from_hub,
            to_hub=to_hub,
            max_link_capacity=max_link_capacity
        )

    def starter_parsing(self, file: str):
        new_c = self.open_file(file)
        i = 1
        has_parsed_drones = False

        for line in new_c:
            line = line.strip()

            if not line or line.startswith("#"):
                i += 1
                continue

            if not has_parsed_drones:
                if not line.startswith("nb_drones"):
                    raise ValueError(
                        f"Parsing Halt (Line {i}): Expected 'nb_drones:' on "
                        "first operational line."
                    )
                try:
                    self.parse_nb_drone(line, i)
                    has_parsed_drones = True
                except ValueError as e:
                    print(f"Fatal Error: {e}")
                    sys.exit(1)
                i += 1
                continue

            if ":" in line:
                prefix, data = line.split(":", 1)
                prefix = prefix.strip()
                data = data.strip()
                try:
                    if prefix in ("start_hub", "end_hub", "hub"):
                        hub_instance = self.hub_parse(data, i)
                        if hub_instance.name in self.hubs:
                            raise ValueError(
                                f"Line {i}: Hub name '{hub_instance.name}' "
                                "already exists."
                            )

                        self.hubs[hub_instance.name] = hub_instance

                        if prefix == "start_hub":
                            if self.start_hub is not None:
                                raise ValueError(
                                    f"Line {i}: Duplicate start_hub found."
                                )
                            self.start_hub = hub_instance
                        elif prefix == "end_hub":
                            if self.end_hub is not None:
                                raise ValueError(
                                    f"Line {i}: Duplicate end_hub found."
                                )
                            self.end_hub = hub_instance

                    elif prefix == "connection":
                        conn = self.connection_parsing(data, i)
                        self.connections.append(conn)

                    elif prefix == "nb_drones":
                        raise ValueError(
                            f"Line {i}: Duplicate definition of drone config."
                        )
                    else:
                        raise ValueError(
                            f"Line {i}: Unknown configuration prefix token "
                            f"'{prefix}'"
                        )

                except ValueError as e:
                    print(f"Fatal Formatting Halt: {e}")
                    sys.exit(1)
            else:
                print(
                    f"Fatal Formatting Halt (Line {i}): Expected a ':' "
                    "syntax assignment structure."
                )
                sys.exit(1)
            i += 1

        if self.start_hub is None:
            print("Fatal Topology Error: Missing unique 'start_hub'.")
            sys.exit(1)
        if self.end_hub is None:
            print("Fatal Topology Error: Missing unique 'end_hub'.")
            sys.exit(1)