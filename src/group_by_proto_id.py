"""Group By Protocol ID - we want to check if the protocol ID is in the list of devices we want to track special.
If so, we publish under a special topic.
"""

import logging

# Add project root to Python path before any local imports
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from managers.device_manager import Device
from managers.protocol_manager import ProtocolManager
from utils.misc_utils import get_project_root, load_json_file

# Local constants - update paths to use project root
project_root = get_project_root()
CONFIG_DIR_PATH = str(project_root / "config")
TRACKED_PROTOCOLS_FILE_NAME = "tracked_protocols.json"
CHECK_INTERVAL_S = 30


class Tracked_Protocols:
    """Manager for protocols we want to track separately"""

    def __init__(
        self,
        config_dir: str = CONFIG_DIR_PATH,
        tracked_protocols_file: str = TRACKED_PROTOCOLS_FILE_NAME,
        check_interval: int = CHECK_INTERVAL_S,
    ):
        self.config_dir = config_dir
        self.tracked_protocols_file = tracked_protocols_file
        self.tracked_protocols_file_path = str(
            Path(self.config_dir) / self.tracked_protocols_file
        )
        self.last_check_time = 0
        self.check_interval = check_interval
        self.tracked_protocols = self._load_tracked_protocols()

    def _load_tracked_protocols(self) -> list:
        """Load tracked protocols from the JSON file"""
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return None

        tracked_protocols: list = []
        file_json = load_json_file(self.tracked_protocols_file_path)
        # see if the key "protocols" exists in the loaded jason
        if "protocols" not in file_json:
            raise ValueError(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                f"Key 'protocols' not found in {self.tracked_protocols_file_path}"
                f"\nfile_json"
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            )
        tracked_protocols = file_json["protocols"]

        return tracked_protocols

    def is_tracked_protocol(self, protocol_id: str) -> bool:
        """Check if protocol ID is a tracked protocol"""
        self._load_tracked_protocols()
        return protocol_id in self.tracked_protocols


# def process_tracked_procotols():
#     """
#     1. Check if the protocol ID is in the list of tracked protocols
#         If not, just return
#     2. If it is, publish under a special topic
#         Topic would be "KTBMES/<source>/tracking/<protocol_id>"
#     """

#     if not Tracked_Protocols.is_tracked_protocol(protocol_id):
#         return


# ###################################################################### #
#                             get_topic_for_device
# ###################################################################### #


def get_topic_for_device(
    device_id: str, device_data: Device, pub_topics: Dict[str, str]
) -> str:
    """
    Get the topic for the device based on the protocol ID.
    """
    topic_root: str = pub_topics["pub_topic_base"]
    protocol_id: str = device_data.protocol_id()

    # Create protocol manager instance
    protocol_manager = ProtocolManager()

    if protocol_manager.is_weather_sensor(protocol_id):
        topic_base = f"{topic_root}/other_weather_sensors"
    elif protocol_manager.is_pressure_sensor(protocol_id):
        topic_base = f"{topic_root}/other_pressure_sensors"
    else:
        topic_base = f"{topic_root}/unknown_other_sensors"
        logging.debug(
            "\n...............................................................\n"
            "get_topic_for_device: Unknown device type\n"
            "\tDevice ID: %s\n"
            "\tDevice Name: %s\n"
            "\tProtocol ID: %s\n"
            "...............................................................\n",
            device_id,
            device_data.device_name(),
            protocol_id,
        )

    return f"{topic_base}/{device_data.device_name()}"
