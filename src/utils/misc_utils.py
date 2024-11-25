import os
import subprocess

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
