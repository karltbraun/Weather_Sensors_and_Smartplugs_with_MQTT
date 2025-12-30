"""misc_utils.py - Utility functions for configuration and environment management.

This module provides utility functions for loading configuration files, environment
variable access, temperature conversion, and system configuration management.

Key Functions:
    - Configuration File Loading: Load and monitor JSON configuration files
    - Environment Variable Access: Get pub source, topic roots, and logging levels
    - Temperature Conversion: Celsius to Fahrenheit conversion
    - Subscription Topics: Parse comma-separated topic lists from environment
    - Configuration Settings: Max backups, retention days, timeouts, intervals

Author: ktb
Updated: 2024-12-30
"""

import json
import os
import subprocess
import time
from typing import Dict

# ###################################################################### #
#                             load_json_file
# ###################################################################### #


def load_json_file(file_path: str) -> Dict[str, Dict]:
    """Load and parse a JSON configuration file.

    Args:
        file_path: Path to the JSON file to load.

    Returns:
        Dictionary containing the parsed JSON data.

    Raises:
        ValueError: If the file cannot be read or contains invalid JSON.

    Example:
        >>> config = load_json_file('./config/local_sensors.json')
    """
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
    """Load JSON configuration file only if it has been modified since last check.

    This function implements efficient configuration reloading by checking file
    modification times and respecting a minimum check interval to avoid excessive
    file system operations.

    Args:
        file_path: Path to the JSON configuration file.
        last_check_time: Unix timestamp of the last check (time.time()).
        check_interval: Minimum seconds between checks (default: 60).

    Returns:
        Dictionary with parsed JSON data if file was modified, None otherwise.

    Example:
        >>> last_check = time.time()
        >>> config = load_configuration_file_on_change(
        ...     './config/sensors.json', last_check, 30
        ... )
    """
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
    """Convert temperature from Celsius to Fahrenheit.

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in degrees Fahrenheit.

    Example:
        >>> celsius_to_fahrenheit(0)
        32.0
        >>> celsius_to_fahrenheit(100)
        212.0
    """
    return (celsius * 9 / 5) + 32


# ###################################################################### #
#                             get_pub_source
# ###################################################################### #


def get_pub_source() -> str:
    """Get the publishing source identifier for this host.

    Retrieves the PUB_SOURCE environment variable, which identifies the
    publishing host in MQTT topics. If not set, falls back to the system
    hostname (with '.local' suffix removed).

    Returns:
        String identifier for the publishing host (e.g., 'ROSA', 'TWIX', 'Mu').

    Environment Variables:
        PUB_SOURCE: Override hostname with explicit identifier.

    Example:
        >>> get_pub_source()
        'ROSA'
    """

    pub_source = os.getenv("PUB_SOURCE", None)
    if pub_source is None:
        # get the hostname from the environment
        pub_source = subprocess.getoutput("hostname").replace(".local", "")

    return pub_source


# ###################################################################### #
#                             get_pub_topic_root
# ###################################################################### #


def get_pub_topic_root() -> str:
    """Get the root MQTT topic for publishing messages.

    Retrieves the PUB_TOPIC_ROOT environment variable, which defines the
    top-level topic for all published messages (e.g., 'KTBMES').

    Returns:
        Root topic string, or 'NONE' if not configured.

    Environment Variables:
        PUB_TOPIC_ROOT: The root topic for all published messages.

    Example:
        >>> get_pub_topic_root()
        'KTBMES'
    """
    my_name = "get_pub_topic_root"
    pub_topic_root = os.getenv("PUB_TOPIC_ROOT", None)
    if pub_topic_root is None:
        pub_topic_root = "NONE"
        print(
            f"{my_name}: PUB_TOPIC_ROOT environment variable not set, using default: {pub_topic_root}"
        )

    return pub_topic_root


# ###################################################################### #
#                             get_sub_topics
# ###################################################################### #


def get_sub_topics(env_var_name: str) -> list:
    """Parse subscription topics from environment variable.

    Reads a comma-separated list of MQTT topics from the specified environment
    variable. If not set, defaults to subscribing to all topics ('#').

    Args:
        env_var_name: Name of the environment variable containing topics
                      (e.g., 'SUB_TOPICS_SENSORS', 'SUB_TOPICS_SHELLY').

    Returns:
        List of topic strings to subscribe to.

    Example:
        >>> get_sub_topics('SUB_TOPICS_SENSORS')
        ['KTBMES/raw/#', 'KTBMES/sensors/#']
        >>> get_sub_topics('UNSET_VAR')
        ['#']
    """

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
    """Get logging configuration from environment variables.

    Retrieves logging settings including console level, file level, and whether
    to clear the log file on startup.

    Returns:
        Dictionary with keys: 'console', 'file', 'clear'.
        Defaults: {'console': 'DEBUG', 'file': 'DEBUG', 'clear': 'True'}

    Environment Variables:
        CONSOLE_LOG_LEVEL: Logging level for console output.
        FILE_LOG_LEVEL: Logging level for file output.
        CLEAR_LOG_FILE: Whether to clear log file on startup ('True'/'False').

    Note:
        TODO: This should return a named tuple instead of a dictionary.

    Example:
        >>> get_logging_levels()
        {'console': 'INFO', 'file': 'DEBUG', 'clear': 'False'}
    """

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
    """Get maximum interval between device republishing.

    Returns:
        Maximum seconds to wait before republishing a device's data,
        even if no new data has been received. Default: 300 seconds (5 minutes).

    Environment Variables:
        PUBLISH_INTERVAL_MAX: Maximum republish interval in seconds.

    Example:
        >>> get_publish_interval_max()
        300
    """
    return int(os.getenv("PUBLISH_INTERVAL_MAX", 300))


# ###################################################################### #
#                             get_config_update_topic
# ###################################################################### #


def get_config_update_topic() -> str:
    """Get MQTT topic for receiving configuration updates.

    Returns:
        MQTT topic where configuration updates are published.

    Raises:
        ValueError: If MQTT_TOPIC_LOCAL_SENSORS_UPDATES is not set.

    Environment Variables:
        MQTT_TOPIC_LOCAL_SENSORS_UPDATES: Topic for sensor config updates.

    Example:
        >>> get_config_update_topic()
        'KTBMES/sensors/config/local_sensors/update'
    """
    topic = os.getenv("MQTT_TOPIC_LOCAL_SENSORS_UPDATES")
    if topic is None:
        raise ValueError(
            "MQTT_TOPIC_LOCAL_SENSORS_UPDATES environment variable is required but not set"
        )
    return topic


# ###################################################################### #
#                             get_backup_settings
# ###################################################################### #


def get_max_backups() -> int:
    """Get maximum number of configuration backup files to retain.

    Returns:
        Maximum number of backup files before old ones are deleted. Default: 10.

    Environment Variables:
        MAX_BACKUPS: Maximum backup files to keep.
    """
    return int(os.getenv("MAX_BACKUPS", 10))


def get_backup_retention_days() -> int:
    """Get number of days to retain configuration backup files.

    Returns:
        Days to keep backup files before deletion. Default: 30 days.

    Environment Variables:
        BACKUP_RETENTION_DAYS: Maximum age of backup files in days.
    """
    return int(os.getenv("BACKUP_RETENTION_DAYS", 30))


# ###################################################################### #
#                             get_config_subscribe_timeout
# ###################################################################### #


def get_config_subscribe_timeout() -> int:
    """Get timeout for waiting on configuration subscription messages.

    This timeout is used when subscribing to the config/current topic to
    determine how long to wait for an existing configuration before assuming
    none exists.

    Returns:
        Timeout in seconds. Default: 10 seconds.

    Environment Variables:
        CONFIG_SUBSCRIBE_TIMEOUT: Subscription timeout in seconds.

    Example:
        >>> get_config_subscribe_timeout()
        10
    """
    return int(os.getenv("CONFIG_SUBSCRIBE_TIMEOUT", 10))
