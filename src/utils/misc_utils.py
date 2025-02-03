import json
import os
import subprocess
import time
from typing import Dict

# ###################################################################### #
#                             load_json_file
# ###################################################################### #


def load_json_file(file_path: str) -> Dict[str, Dict]:
    """Load information  from a JSON file specified by the file_path argument"""
    my_name = "load_json_file"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as ex:
        raise ValueError(
            f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"{my_name}: Error decoding JSON from {file_path}: {ex}"
            f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        ) from ex
    except (OSError, IOError) as ex:
        raise ValueError(
            f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"{my_name}: Error loading file {file_path}: {ex}"
            f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        ) from ex


def load_configuration_file_on_change(
    file_path: str, last_check_time: float, check_interval: int = 60
) -> Dict[str, Dict]:
    """Load information from a JSON file specified by the file_path argument
    if sufficient time has passed to warrant a check for changes, AND
    if the file has changed since the last check."""
    current_time = time.time()
    if current_time - last_check_time < check_interval:
        return None
    # determine if the file has changed
    file_stat = os.stat(file_path)
    if file_stat.st_mtime <= last_check_time:
        return None
    return load_json_file(file_path)


# ###################################################################### #
#                          celsius_to_fahrenheit
# ###################################################################### #


def celsius_to_fahrenheit(celsius: float) -> float:
    """convert celsius to fahrenheit"""
    return (celsius * 9 / 5) + 32


# ###################################################################### #
#                             get_pub_source
# ###################################################################### #


def get_pub_source() -> str:
    """get the hostname of the publishing device"""

    pub_source = os.getenv("PUB_SOURCE", None)
    if pub_source is None:
        # get the hostname from the environment
        pub_source = subprocess.getoutput("hostname").replace(".local", "")

    return pub_source


# ###################################################################### #
#                             get_pub_root
# ###################################################################### #


def get_pub_root() -> str:
    """get the root (top-level) of the publication topic"""

    pub_source = os.getenv("PUB_ROOT", None)
    if pub_source is None:
        # get the hostname from the environment
        pub_source = "enterprise"

    return pub_source


# ###################################################################### #
#                             get_sub_topics
# ###################################################################### #


def get_sub_topics(env_var_name: str) -> list:
    """Get the subscription topics from the specified environment variable."""

    env_sub_topics = os.getenv(env_var_name, None)
    if env_sub_topics is None:
        # Default to subscribing to all topics
        sub_topics = ["#"]
    else:
        sub_topics = env_sub_topics.split(",")

    return sub_topics


# ###################################################################### #
#                             get_logging_levels
# ###################################################################### #


def get_logging_levels() -> dict:
    """Get the logging levels from the environment variables."""

    log_levels = {
        "console": os.getenv("CONSOLE_LOG_LEVEL", "DEBUG"),
        "file": os.getenv("FILE_LOG_LEVEL", "DEBUG"),
        "clear": os.getenv("CLEAR_LOG_FILE", "True"),
    }

    return log_levels


# ###################################################################### #
#                             get_publish_interval_max
# ###################################################################### #


def get_publish_interval_max() -> int:
    """Get the maximum publish interval from the environment variables."""
    # default to 5 minutes
    return int(os.getenv("PUBLISH_INTERVAL_MAX", 300))
