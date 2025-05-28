"""
logic to dump the data into a file
"""

import json
import os
import time
from pathlib import Path

from src.managers.device_manager import Device

# make sure load_dotenv is called before this


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Device):
            return obj.device  # Return the internal dictionary
        # Call the parent class's default() method first
        try:
            return super().default(obj)
        except TypeError:
            return str(
                obj
            )  # Convert any other non-serializable objects to strings


class DataRepositoryManager:
    def __init__(
        self, dump_dir: str, dump_file: str, dump_interval: int = 60
    ):
        self.dump_dir = dump_dir
        self.dump_file = dump_file
        self.dump_file_path = str(Path(dump_dir) / dump_file)
        self.dump_interval = dump_interval
        self.last_dump_time = 0.0

        # Ensure directory exists
        os.makedirs(self.dump_dir, exist_ok=True)

    def dump_data(self, data: dict, filepath: str | None = None) -> None:
        """
        Dump data to a JSON file if enough time has elapsed since the last dump.

        Args:
            data: Dictionary of data to dump
            filepath: Optional filepath to dump to. Defaults to self.dump_file_path
        """
        current_time = time.time()
        if current_time - self.last_dump_time < self.dump_interval:
            return

        filepath = filepath or self.dump_file_path
        if not filepath:
            raise ValueError("No valid filepath provided for data dump")

        # Convert the devices dictionary to a serializable format
        serializable_data = {}
        for key, device in data.items():
            serializable_data[key] = (
                device.device
            )  # Access the internal dictionary directly

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(serializable_data, file, indent=4)

        self.last_dump_time = current_time
