import json
import os
import sys

# We define the file name here
CONFIG_FILE = "config.json"

def load_config():
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "config.json")
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
            
    except FileNotFoundError:
        print("ERROR: config.json not found!")
        return None
    except json.JSONDecodeError:
        print("ERROR: JSON Error {e}")
        return None
    
CONFIG = load_config()

if CONFIG is None:
    sys.exit(1)