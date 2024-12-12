import os
import time
from typing import Dict

from src.utils.misc_utils import load_json_file


class ConfigurationFileManager:
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
