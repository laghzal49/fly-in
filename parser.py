import sys

class Parser:
    def __init__(self, file_name):
        self.file_name = file_name
        self.start_hub = None
        self.end_hub = None
        self.hubs = dict()
        self.connections = []
        

    def open_file(self):
        try:
            with open(self.file_name, "r+") as file:
                content = file.readlines()
                return content
        except FileNotFoundError:
            raise FileNotFoundError("Error in Finding the file")
        except PermissionError:
            raise PermissionError
#fuck u
    def check_content(self):
        content = self.open_file()
        for i, cont in enumerate(content):
           if (cont.strip() or cont.strip('\n')):
              continue
           if (cont.startswith("#")):
              continue
           if (cont.startswith("start_hub")):
              if (self.start_hub == None):
                 self.start_hub = cont.split()[1]
              else:
                 raise ValueError("Multiple start_hub lines found")
           if (cont.startswith("end_hub")):
              if (self.end_hub == None):
                 self.end_hub = cont.split()[1]
              else:
                 raise ValueError("Multiple end_hub lines found")
              continue
           if (cont.startswith("hub")):
              self.hubs[cont.split()[1]] = cont.split()[2]
              continue
           if (cont.startswith("connect")):
              self.connections.append(cont.split()[1:])
              continue
           
try:
    tarik = Parser(sys.argv[1])
    tarik.check_content()
except Exception as e:
    print(e)
