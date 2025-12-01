"""
local_sensor_manager.py - manages list of local sensors
(vs. others in the area that RTL_433 picks up)

Enhanced with dynamic MQTT-based configuration updates
"""

import json
import logging
import os
import shutil
import time
from datetime import datetime
from typing import Dict, Optional, Tuple, Union

from src.utils.misc_utils import (
    get_backup_retention_days,
    get_config_update_topic,
    get_max_backups,
    load_json_file,
)


class LocalSensorManager:
    """
    Local Sensor Manager to handle local sensors with dynamic MQTT-based updates

    Features:
    - Load/reload sensor configurations from JSON file
    - Handle MQTT-based dynamic configuration updates
    - Support merge and replace update modes
    - Automatic backup creation before updates
    - Comprehensive validation and error handling
    """

    def __init__(
        self,
        config_dir: str = "./config",
        sensors_file: str = "local_sensors.json",
        check_interval: int = 60,
        max_backups: Optional[int] = None,
        backup_retention_days: Optional[int] = None,
    ):
        self.config_dir = config_dir
        self.sensors_file = sensors_file
        self.last_check_time = 0
        self.check_interval = check_interval
        self.max_backups = max_backups if max_backups is not None else get_max_backups()
        self.backup_retention_days = backup_retention_days if backup_retention_days is not None else get_backup_retention_days()
        self.sensors = self._load_sensors()
        self.logger = logging.getLogger(__name__)

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

    def get_file_path(self) -> str:
        """Get the full file path for the sensors configuration file"""
        return os.path.join(self.config_dir, self.sensors_file)

    def create_backup(self) -> Optional[str]:
        """
        Create a timestamped backup of the current local_sensors.json file

        Returns:
            str: Path to backup file if successful, None if failed
        """
        try:
            source_path = self.get_file_path()
            if not os.path.exists(source_path):
                self.logger.warning(
                    f"Source file does not exist: {source_path}"
                )
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{self.sensors_file}.backup.{timestamp}"
            backup_path = os.path.join(self.config_dir, backup_filename)

            shutil.copy2(source_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            
            # Clean up old backups after creating new one
            self.cleanup_old_backups()
            
            return backup_path

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None

    def cleanup_old_backups(self) -> None:
        """
        Clean up old backup files based on retention policies:
        - Keep only the most recent max_backups files
        - Remove files older than backup_retention_days
        """
        try:
            backup_pattern = f"{self.sensors_file}.backup."
            backup_files = []
            
            # Find all backup files
            for filename in os.listdir(self.config_dir):
                if filename.startswith(backup_pattern):
                    filepath = os.path.join(self.config_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        backup_files.append({
                            'path': filepath,
                            'filename': filename,
                            'mtime': stat.st_mtime
                        })
            
            if not backup_files:
                return
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x['mtime'], reverse=True)
            
            removed_count = 0
            current_time = time.time()
            retention_seconds = self.backup_retention_days * 24 * 3600
            
            for i, backup in enumerate(backup_files):
                should_remove = False
                reason = ""
                
                # Remove if beyond max_backups limit
                if i >= self.max_backups:
                    should_remove = True
                    reason = f"exceeds max backup limit ({self.max_backups})"
                
                # Remove if older than retention period
                elif (current_time - backup['mtime']) > retention_seconds:
                    should_remove = True
                    reason = f"older than {self.backup_retention_days} days"
                
                if should_remove:
                    try:
                        os.remove(backup['path'])
                        removed_count += 1
                        self.logger.info(
                            f"Removed backup {backup['filename']}: {reason}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to remove backup {backup['filename']}: {e}"
                        )
            
            if removed_count > 0:
                self.logger.info(f"Cleanup completed: removed {removed_count} backup files")
            
        except Exception as e:
            self.logger.error(f"Error during backup cleanup: {e}")

    def validate_sensor_data(self, sensor_data: Dict) -> Tuple[bool, str]:
        """
        Validate sensor data structure and content

        Args:
            sensor_data: Dictionary containing sensor configuration

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not isinstance(sensor_data, dict):
                return False, "Sensor data must be a dictionary"

            for sensor_id, sensor_info in sensor_data.items():
                # Validate sensor ID
                if not isinstance(sensor_id, str) or not sensor_id.strip():
                    return False, f"Invalid sensor ID: {sensor_id}"

                # Validate sensor info structure
                if not isinstance(sensor_info, dict):
                    return (
                        False,
                        f"Sensor info for ID {sensor_id} must be a dictionary",
                    )

                # Check required fields
                required_fields = ["sensor_name", "id_sensor_name"]
                for field in required_fields:
                    if field not in sensor_info:
                        return (
                            False,
                            f"Missing required field '{field}' for sensor ID {sensor_id}",
                        )

                    if not isinstance(sensor_info[field], str):
                        return (
                            False,
                            f"Field '{field}' for sensor ID {sensor_id} must be a string",
                        )

                # Validate optional comment field
                if "comment" in sensor_info and not isinstance(
                    sensor_info["comment"], str
                ):
                    return (
                        False,
                        f"Comment field for sensor ID {sensor_id} must be a string",
                    )

            return True, "Validation successful"

        except Exception as e:
            return False, f"Validation error: {e}"

    def write_sensors_to_file(self, sensor_data: Dict) -> bool:
        """
        Write sensor data to the JSON file

        Args:
            sensor_data: Dictionary containing sensor configuration

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = self.get_file_path()

            # Ensure directory exists
            os.makedirs(self.config_dir, exist_ok=True)

            # Write JSON file with proper formatting
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sensor_data, f, indent=4, ensure_ascii=False)

            self.logger.info(
                f"Successfully wrote {len(sensor_data)} sensors to {file_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to write sensors to file: {e}")
            return False

    def reload_sensors(self) -> bool:
        """
        Reload sensors from file and update in-memory cache

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = self.get_file_path()
            new_sensors = load_json_file(file_path)

            if new_sensors is not None:
                self.sensors = new_sensors
                self.last_check_time = time.time()
                self.logger.info(
                    f"Reloaded {len(self.sensors)} sensors from file"
                )
                return True
            else:
                self.logger.error("Failed to load sensors from file")
                return False

        except Exception as e:
            self.logger.error(f"Failed to reload sensors: {e}")
            return False

    def handle_config_update(
        self, payload: Union[str, bytes, Dict]
    ) -> Tuple[bool, str]:
        """
        Handle MQTT configuration update message

        Args:
            payload: MQTT message payload (JSON string, bytes, or dict)
            Update local sensors configuration from MQTT payload (always replaces existing config)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Parse payload if it's not already a dict
            if isinstance(payload, (str, bytes)):
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                update_data = json.loads(payload)
            elif isinstance(payload, dict):
                update_data = payload
            else:
                return False, f"Invalid payload type: {type(payload)}"

            self.logger.info(
                f"Processing config update: replacing sensors with {len(update_data)} entries"
            )

            # Validate the update data
            is_valid, validation_msg = self.validate_sensor_data(
                update_data
            )
            if not is_valid:
                return False, f"Validation failed: {validation_msg}"

            # Create backup before making changes
            backup_path = self.create_backup()
            if backup_path is None:
                self.logger.warning(
                    "Could not create backup, proceeding anyway"
                )

            # Always replace entire sensor configuration
            new_sensors = update_data.copy()

            # Write updated configuration to file
            if not self.write_sensors_to_file(new_sensors):
                return (
                    False,
                    "Failed to write updated configuration to file",
                )

            # Reload in-memory cache
            if not self.reload_sensors():
                return False, "Failed to reload configuration after update"

            success_msg = (
                f"Successfully updated local sensors: replaced with {len(update_data)} entries, total={len(self.sensors)}"
            )
            self.logger.info(success_msg)

            return True, success_msg

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON payload: {e}"
            self.logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Config update failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def get_update_topic(self) -> str:
        """Get the MQTT topic for configuration updates"""
        return get_config_update_topic()

    def get_sensor_count(self) -> int:
        """Get the current number of configured sensors"""
        return len(self.sensors) if self.sensors else 0

    def get_all_sensor_ids(self) -> list:
        """Get list of all configured sensor IDs"""
        return list(self.sensors.keys()) if self.sensors else []
