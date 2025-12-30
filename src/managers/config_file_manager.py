"""config_file_manager.py - Generic configuration file management.

This module provides the ConfigurationFileManager class for loading and
monitoring JSON configuration files with automatic reload on modification.

Author: ktb
Updated: 2024-12-30
"""

import os
import time
from typing import Dict

from src.utils.misc_utils import load_json_file


class ConfigurationFileManager:
    """Manages JSON configuration file loading with change detection.

    Monitors a JSON configuration file and reloads it only when modified,
    respecting a minimum check interval to avoid excessive file system operations.

    Attributes:
        config_dir: Directory containing configuration files.
        config_file: Configuration filename.
        file_path: Full path to configuration file.
        check_interval: Minimum seconds between file modification checks.
        last_check_time: Unix timestamp of last check.
        last_load_time: Unix timestamp of last load.
        last_modified_time: Unix timestamp of file's last modification.
        configuration: Cached configuration dictionary.

    Example:
        >>> manager = ConfigurationFileManager(
        ...     config_file='protocols.json',
        ...     config_dir='./config',
        ...     check_interval=60
        ... )
        >>> config = manager._load_configuration()
    """

    def __init__(
        self,
        config_file: str,
        config_dir: str = "./config",
        check_interval: int = 60,
    ):
        # directory containing config files
        self.config_dir: str = config_dir
        # configuration file name
        self.config_file: str = config_file
        # full path to configuration file
        self.file_path: str = os.path.join(
            self.config_dir, self.config_file
        )
        # number of seconds between checks for changes
        self.check_interval: int = check_interval
        # last time configuration file was checked
        self.last_check_time: float = 0
        # last time configuration file was loaded
        self.last_load_time: float = 0
        # last time configuration file was modified
        self.last_modified_time: float = 0
        # actual configuration data
        self.configuration: dict = {}

    def _load_configuration(self) -> Dict[str, Dict]:
        """Load configuration if file has been modified since last check.

        Checks if enough time has passed since last check and if the file
        has been modified since last load. Only reloads if both conditions
        are met.

        Returns:
            Configuration dictionary (possibly cached from previous load).

        Raises:
            ValueError: If configuration file does not exist.
        """
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return self.configuration

        try:
            modified_time = os.path.getmtime(self.file_path)
        except FileNotFoundError:
            raise ValueError(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                f"Configuration file {self.file_path} not found"
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            )

        if modified_time > self.last_modified_time:
            self.configuration = load_json_file(self.file_path)
            self.last_modified_time = modified_time
            self.last_load_time = current_time

        self.last_check_time = current_time
        return self.configuration
