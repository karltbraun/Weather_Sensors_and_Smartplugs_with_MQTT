"""
broker_config.py

This module contains the MQTT Broker Configuration Constants.
It loads default values from mqtt_config and updates them with
environment variables if available.
"""

import json
import os

# get normal default values from mqtt_config
from config.mqtt_config import MQTT_DEFAULT_KEEPALIVE, MQTT_DEFAULT_PORT

MY_NAME = "broker_config"

# MQTT_CONFIG dictionary
#   Note that hostnames beginning with "TS-" are for Tailscale VPN addresses versions
#   of those hosts.

BROKER_CONFIG = {
    "TS-VULTR1": {
        "MQTT_BROKER_ADDRESS": "100.76.195.63",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "PI-02": {
        "MQTT_BROKER_ADDRESS": "10.24.94.78",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
}


def load_broker_config():
    """
    Load MQTT_CONFIG_INFO from environment variable and update BROKER_CONFIG.
    """
    my_name = "load_broker_config"

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
