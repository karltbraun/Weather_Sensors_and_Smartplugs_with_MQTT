"""
logic to dump the data into a file
"""

import json
import time

from src.managers.device_manager import Device

# make sure load_dotenv is called before this


class DataRepositoryManager:
    def __init__(
        self, dump_file_dir: str, dump_file_name: str, dump_interval: float
    ):
        self.dump_file_dir: str = dump_file_dir
        self.dump_file_name: str = dump_file_name
        self.dump_file_path: str = f"{dump_file_dir}/{dump_file_name}"
        self.dump_interval: float = dump_interval
        self.last_dump_time: float = 0.0

    def dump_data(self, data: dict, filename: str):
        current_time = time.time()
        if current_time - self.last_dump_time < self.dump_interval:
            return

        with open(filename, "w") as file:
            json.dump(data, file, indent=4, cls=CustomJSONEncoder)

        self.last_dump_time = current_time


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Device):
            return obj.__dict__  # Convert Device object to a dictionary
        if isinstance(obj, dict):
            return obj
        # Add other custom serialization logic here if needed
        return super().default(obj)
