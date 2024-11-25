"""protocol_manager.py
Protocol Manager to handle RTL_433 protocols
"""

import json
import time
from typing import Dict

# ###################################################################### #
#                             load_protocols
# ###################################################################### #


def load_json_file(file_path: str) -> Dict[str, Dict]:
    """Load protocols from a JSON file specified by the file_path argument"""
    my_name = "load_protocols"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as ex:
        raise ValueError(
            f"{my_name}: Error decoding JSON from {file_path}: {ex}"
        ) from ex
    except (OSError, IOError) as ex:
        raise ValueError(
            f"{my_name}: Error loading file {file_path}: {ex}"
        ) from ex


# ###################################################################### #
#                      ProtocolManager Class
# ###################################################################### #


class ProtocolManager:
    """Protocol Manager to handle RTL_433 protocols"""

    def __init__(
        self,
        config_dir: str = "./config",
        protocols_file: str = "rtl_433_protocols.json",
        categories_file: str = "protocol_categories.json",
    ):
        # configuration file paths
        self.config_dir = config_dir
        self.protocols_file = protocols_file
        self.categories_file = categories_file
        # device attributes
        self.protocols = self._load_protocols()
        self.categories = self._load_categories()
        self.last_check_time = 0
        self.check_interval = 60  # Check every 60 seconds

    # ############################ _load_protocols ############################ #

    def _load_protocols(self) -> Dict[str, Dict]:
        """Load protocols from the JSON file"""
        file_path = f"{self.config_dir}/{self.protocols_file}"
        return load_json_file(file_path)

    # ############################ _load_categories ############################ #

    def _load_categories(self) -> Dict[str, Dict]:
        """Load categories from the JSON file"""
        file_path = f"{self.config_dir}/{self.categories_file}"
        return load_json_file(file_path)

    # ############################ _load_iconfigurations ############################ #

    def _load_configurations(self) -> None:
        """Load configurations if files have been modified"""
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return

        # json load error checking done in load_json_file, called by both _load methods
        self.protocols = self._load_protocols()
        self.categories = self._load_categories()
        self.last_check_time = current_time

    # ############################ get_protocl_info ############################ #

    def get_protocol_info(self, protocol_id: str) -> Dict[str, str]:
        """Get the protocol information for a protocol ID"""
        self._load_configurations()
        return self.protocols.get(str(protocol_id), {})

    # ############################ is_weather_sensor ############################ #

    def is_weather_sensor(self, protocol_id: str) -> bool:
        """Check if protocol ID is for a weather sensor"""
        self._load_configurations()
        return protocol_id in self.categories.get(
            "weather_sensor_protocol_ids", []
        )

    # ############################ is_unk_weather_sensor ############################ #

    def is_unk_weather_sensor(self, protocol_id: str) -> bool:
        """Check if protocol ID is for a pressure sensor"""
        self._load_configurations()
        return protocol_id in self.categories.get("pressure_sensors", [])

    # ############################ is_pressure_sensor ############################ #

    def is_pressure_sensor(self, protocol_id: str) -> bool:
        """Check if protocol ID is for a pressure sensor"""
        self._load_configurations()
        return protocol_id in self.categories.get(
            "pressure_sensor_protocol_ids", []
        )
