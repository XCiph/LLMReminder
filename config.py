import json
import os

CONFIG_PATH = "config.json"

def get_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
