import re
import sys


HUB_PATTERN = r"([A-Za-z_]\w*)\s+(-?\d+)\s+(-?\d+)"


class Parser:
    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hubs = []

    def open_file(self, file: str):
        try:
            with open(file, "r") as f:
                content = f.readlines()
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file} not found.")
        except FileExistsError:
            raise FileExistsError(f"File {file} already exists.")
        except Exception as e:
            raise Exception(f"An error occurred while opening the file: {e}")

    def parse_file(self, file: str):
        content = self.open_file(file)

        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hubs = []

        i = 0
        while i < len(content):
            line = content[i].strip()

            if line.startswith("#") or line == "":
                i += 1
                continue

            if line.startswith("nb_drones"):
                result = re.match(r"nb_drones:\s*(\d+)", line)
                if result:
                    self.nb_drones = int(result.group(1))
            elif line.startswith("start_hub"):
                if self.start_hub is not None:
                    raise ValueError("Multiple start_hub entries found.")
                result = re.match(rf"start_hub:\s*{HUB_PATTERN}", line)
                if result:
                    self.start_hub = result.group(1)
                    self.hubs.append(
                        {
                            "name": self.start_hub,
                            "x": int(result.group(2)),
                            "y": int(result.group(3)),
                        }
                    )
            elif line.startswith("end_hub"):
                if self.end_hub is not None:
                    raise ValueError("Multiple end_hub entries found.")
                result = re.match(rf"end_hub:\s*{HUB_PATTERN}", line)
                if result:
                    self.end_hub = result.group(1)
                    self.hubs.append(
                        {
                            "name": self.end_hub,
                            "x": int(result.group(2)),
                            "y": int(result.group(3)),
                        }
                    )
            elif line.startswith("hub"):
                result = re.match(rf"hub:\s*{HUB_PATTERN}", line)
                if result:

                    self.hubs.append(
                        {
                            "name": result.group(1),
                            "x": int(result.group(2)),
                            "y": int(result.group(3)),
                        }
                    )
            i += 1


if __name__ == "__main__":
    try:
        file = sys.argv[1] if len(sys.argv) > 1 else "map.txt"
        parser = Parser()
        parser.parse_file(file)
        print(f"Number of drones: {parser.nb_drones}")
        print(f"Start hub: {parser.start_hub}")
        print(f"End hub: {parser.end_hub}")
        print("Hubs:")
        for hub in parser.hubs:
            print(f"{hub['name']}: ({hub['x']}, {hub['y']})")
    except Exception as e:
        print(f"An error occurred: {e}")
