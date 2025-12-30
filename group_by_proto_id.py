"""Group By Protocol ID - we want to check if the protocol ID is in the list of devices we want to track special.
If so, we publish under a special topic.
"""

import time
from typing import Dict, Tuple

from src.utils.misc_utils import load_json_file

#
# local constants
#

CONFIG_DIR_PATH = "./config"
TRACKED_PROTOCOLS_FILE_NAME = "tracked_protocols.json"
CHECK_INTERVAL_S = 30


class Tracked_Protocols:
    """Manager for tracking and categorizing RTL-433 protocols.

    Maintains a list of protocol IDs that should receive special handling
    or categorization in the sensor processing pipeline.

    Attributes:
        config_dir: Directory containing protocol configuration.
        tracked_protocols_file: Filename of tracked protocols JSON.
        tracked_protocols_file_path: Full path to config file.
        last_check_time: Unix timestamp of last config check.
        check_interval: Seconds between configuration checks.
        tracked_protocols: List of protocol IDs to track.

    Configuration File Format:
        {
            "protocols": [181, 40, 55, ...]
        }

    Example:
        >>> tracker = Tracked_Protocols()
        >>> protocols = tracker._load_tracked_protocols()
    """

    def __init__(
        self,
        config_dir: str = CONFIG_DIR_PATH,
        tracked_protocols_file: str = TRACKED_PROTOCOLS_FILE_NAME,
        check_interval: int = CHECK_INTERVAL_S,
    ):
        self.config_dir = config_dir
        self.tracked_protocols_file = tracked_protocols_file
        self.tracked_protocols_file_path = (
            f"{self.config_dir}/{self.tracked_protocols_file}"
        )
        self.last_check_time = 0
        self.check_interval = check_interval
        self.tracked_protocols = self._load_tracked_protocols()

    def _load_tracked_protocols(self) -> list:
        """Load tracked protocol IDs from configuration file.

        Reads the tracked_protocols.json file and extracts the list of
        protocol IDs. Implements interval-based checking to avoid excessive
        file reads.

        Returns:
            List of protocol IDs (integers) to track, or None if check
            interval not exceeded.

        Raises:
            ValueError: If 'protocols' key not found in configuration file.
        """
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


def process_tracked_procotols():
    """
    1. Check if the protocol ID is in the list of tracked protocols
        If not, just return
    2. If it is, publish under a special topic
        Topic would be "KTBMES/<source>/tracking/<protocol_id>"
    """

    if not Tracked_Protocols.is_tracked_protocol(protocol_id):
        return


# ###################################################################### #
#                             get_topic_for_device
# ###################################################################### #


def get_topic_for_device(
    device_id: str, device_data: Device, pub_topics: Dict[str, str]
) -> str:
    """
    Get the topic for the device based on the protocol ID.
    """
    # my_name = "get_topic_for_device"

    topic_root: str = pub_topics["pub_topic_base"]

    # protocol_id: str = get_protocol_id(device_data)
    protocol_id: str = device_data.protocol_id()

    # KTBMES/<source>/tracking/<protocol_id>

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

    topic = f"{topic_base}/{device_data.device_name()}"

    return topic
