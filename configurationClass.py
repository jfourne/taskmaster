import re
import os
import json

class ConfigurationFile:

    path = str()
    parsed_file = dict()

    def __init__(self, conf_path="./taskmasterd.conf"):
        
        self.path = conf_path
        if self.parseJSON() != 0:
            print("ParseError: {}: wrong configuration file" .format(self.path))
        return None

    def parseJSON(self):
        
        try:
            with open(self.path, "r") as open_file:
                encodedJSON = open_file.read()
                self.parsed_file = json.loads(encodedJSON)
                return 0
        except:
            print("Error: can't open file {}" .format(self.path))
            return 1
