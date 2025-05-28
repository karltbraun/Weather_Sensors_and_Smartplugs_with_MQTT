"""
local_sensor_manager.py - manages list of local sensors
(vs. others in the area that RTL_433 picks up)
"""

import time
from typing import Dict, Tuple

from ..utils.misc_utils import load_json_file


class LocalSensorManager:
    """Local Sensor Manager to handle local sensors"""

    def __init__(
        self,
        config_dir: str = "./config",
        sensors_file: str = "local_sensors.json",
        check_interval: int = 60,
    ):
        self.config_dir = config_dir
        self.sensors_file = sensors_file
        self.last_check_time = 0
        self.check_interval = check_interval
        self.sensors = self._load_sensors()

    def _load_sensors(self) -> Dict[str, Dict]:
        """Load local sensors from the JSON file"""
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return

        file_path = f"{self.config_dir}/{self.sensors_file}"
        return load_json_file(file_path)

    def is_local_sensor(self, sensor_id: str) -> bool:
        """Check if sensor ID is a local sensor"""
        return sensor_id in self.sensors

    def sensor_name(self, sensor_id: str) -> str:
        """Get the sensor name for a local sensor"""
        return self.sensors.get(sensor_id, {}).get("sensor_name", None)

    def id_sensor_name(self, sensor_id: str) -> str:
        """Get the sensor name for a local sensor"""
        return self.sensors.get(sensor_id, {}).get("id_sensor_name", None)

    def sensor_info(self, sensor_id: str) -> Tuple[str, str, str]:
        """Get the sensor name, id_sensor_name, and comment data for a local sensor"""
        if (sensor := self.sensors.get(sensor_id, None)) is None:
            raise ValueError(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                f"Sensor ID {sensor_id} not found in local sensors"
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            )

        return (
            sensor.get("sensor_name", None),
            sensor.get("id_sensor_name", None),
            sensor.get("comment", None),
        )
