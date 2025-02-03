"""
broker_config.py

This module contains the MQTT Broker Configuration Constants.
It loads default values from mqtt_config and updates them with
environment variables if available.
"""

import json
import os

from dotenv import load_dotenv

# get normal default values from mqtt_config
from config.mqtt_config import MQTT_DEFAULT_KEEPALIVE, MQTT_DEFAULT_PORT

MY_NAME = "broker_config"

# MQTT_CONFIG dictionary
#   Note that hostnames beginning with "TS-" are for Tailscale VPN addresses versions
#   of those hosts.

BROKER_CONFIG = {
    "n-vultr1": {
        "MQTT_BROKER_ADDRESS": "n-vultr1",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "TS-VULTR1": {
        "MQTT_BROKER_ADDRESS": "TS-Vultr1",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "PI2": {
        "MQTT_BROKER_ADDRESS": "pi2",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "TS-PI2": {
        "MQTT_BROKER_ADDRESS": "pi2",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "mqtt.eclipse.org": {
        "MQTT_BROKER_ADDRESS": "mqtt.eclipse.org",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
}

# broker to use if no other is specified
DEFAULT_BROKER_NAME = "mqtt.eclipse.org"


# ###################################################################### #
#                          load_broker_config
# ###################################################################### #


def load_broker_config() -> dict:
    """
    Load MQTT_CONFIG_INFO from environment variable and update BROKER_CONFIG.
    """
    my_name = "load_broker_config"
    load_dotenv()

    #
    # configure secrets in BROKER_CONFIG from environment variables
    #

    mqtt_config_info_str = os.getenv("MQTT_CONFIG_INFO")
    if mqtt_config_info_str is None:
        raise ValueError(
            f"{my_name}: MQTT_CONFIG_INFO environment variable is not set"
        )
    try:
        mqtt_config_info = json.loads(mqtt_config_info_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{my_name}: MQTT_CONFIG_INFO environment variable is not valid JSON"
        ) from exc

    # Update MQTT_CONFIG with values from environment variables
    for key, config in BROKER_CONFIG.items():
        if key in mqtt_config_info:
            config["MQTT_USERNAME"] = mqtt_config_info[key][
                "MQTT_USERNAME"
            ]
            config["MQTT_PASSWORD"] = mqtt_config_info[key][
                "MQTT_PASSWORD"
            ]

    #
    # Update BROKER_NAME from environment variable
    #

    broker_name = os.getenv("BROKER_NAME", DEFAULT_BROKER_NAME)
    broker_config = BROKER_CONFIG.get(broker_name)
    print(f"{my_name}: Using broker {broker_name}")
    print(f"\t{broker_config}")

    return broker_name
