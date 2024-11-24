import os
import subprocess

# ###################################################################### #
#                          celsius_to_fahrenheit
# ###################################################################### #


def celsius_to_fahrenheit(self, celsius: float) -> float:
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


def get_sub_topics_shelly() -> list:
    """get the subscription topics for the shelly devices"""

    env_sub_topics = os.getenv("SUB_TOPICS_SHELLY", None)
    if env_sub_topics is None:
        # get the hostname from the environment
        sub_topics = ["#"]
    else:
        sub_topics = env_sub_topics.split(",")

    return sub_topics
