"""data_repository_manager.py - Device data persistence management.

This module provides the DataRepositoryManager class for periodically persisting
device data to JSON files with configurable dump intervals.

Author: ktb
Updated: 2024-12-30
"""

import json
import os
import time

from src.managers.device_manager import Device

# make sure load_dotenv is called before this


class DataRepositoryManager:
    """Manages periodic data persistence to JSON files.

    Provides throttled data dumping with configurable intervals to avoid
    excessive disk I/O while ensuring data is regularly persisted.

    Attributes:
        dump_file_dir: Directory for output files.
        dump_file_name: Default output filename.
        dump_file_path: Full path to default output file.
        dump_interval: Minimum seconds between dumps.
        last_dump_time: Unix timestamp of last dump operation.

    Example:
        >>> manager = DataRepositoryManager('data', 'devices.json', 60)
        >>> manager.dump_data(devices_dict, 'data/devices.json')
    """

    def __init__(
        self, dump_file_dir: str, dump_file_name: str, dump_interval: float
    ):
        """Initialize the data repository manager.

        Args:
            dump_file_dir: Directory path for output files.
            dump_file_name: Default filename for data dumps.
            dump_interval: Minimum seconds between dump operations.

        Note:
            Creates dump_file_dir if it doesn't exist.
        """
        self.dump_file_dir: str = dump_file_dir
        self.dump_file_name: str = dump_file_name
        self.dump_file_path: str = f"{dump_file_dir}/{dump_file_name}"
        self.dump_interval: float = dump_interval
        self.last_dump_time: float = 0.0

        # Ensure directory exists
        os.makedirs(self.dump_file_dir, exist_ok=True)

    def dump_data(self, data: dict, filename: str):
        """Write device data to JSON file with interval throttling.

        Args:
            data: Dictionary of device data to persist.
            filename: Output file path (can include directories).

        Note:
            - Only dumps if dump_interval seconds have passed since last dump
            - Creates parent directories if they don't exist
            - Uses CustomJSONEncoder for Device object serialization
        """
        current_time = time.time()
        if current_time - self.last_dump_time < self.dump_interval:
            return

        # Ensure the directory for this specific file exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w") as file:
            json.dump(data, file, indent=4, cls=CustomJSONEncoder)

        self.last_dump_time = current_time


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Device objects and dictionaries.

    Extends json.JSONEncoder to handle Device instances by converting them
    to their underlying dictionary representation.

    Example:
        >>> json.dumps(device_data, cls=CustomJSONEncoder)
    """

    def default(self, obj):
        if isinstance(obj, Device):
            return obj.__dict__  # Convert Device object to a dictionary
        if isinstance(obj, dict):
            return obj
        # Add other custom serialization logic here if needed
        return super().default(obj)
