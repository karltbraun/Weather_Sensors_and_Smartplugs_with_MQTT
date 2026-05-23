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
    "n-vultr3": {
        "MQTT_BROKER_ADDRESS": "n-vultr3",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "ts-vultr3": {
        "MQTT_BROKER_ADDRESS": "vultr3",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "TS-vultr3": {
        "MQTT_BROKER_ADDRESS": "vultr3",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "n-vultr2": {
        "MQTT_BROKER_ADDRESS": "n-vultr2",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
    "ts-vultr2": {
        "MQTT_BROKER_ADDRESS": "vultr2",
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
    "local": {
        "MQTT_BROKER_ADDRESS": "localhost",
        "MQTT_BROKER_PORT": MQTT_DEFAULT_PORT,
        "MQTT_USERNAME": "",
        "MQTT_PASSWORD": "",
        "MQTT_KEEPALIVE": MQTT_DEFAULT_KEEPALIVE,
    },
}

# broker to use if no other is specified
DEFAULT_BROKER_NAME = "mqtt.eclipse.org"


def _int_from_env(var_name: str, default: int) -> int:
    """Read an integer environment variable with a safe default."""
    value = os.getenv(var_name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _build_env_fallback_config() -> dict | None:
    """Build broker configuration directly from MQTT_* environment variables."""
    broker_address = os.getenv("MQTT_BROKER_ADDRESS")
    if not broker_address:
        return None

    return {
        "MQTT_BROKER_ADDRESS": broker_address,
        "MQTT_BROKER_PORT": _int_from_env(
            "MQTT_BROKER_PORT", MQTT_DEFAULT_PORT
        ),
        "MQTT_USERNAME": os.getenv("MQTT_USERNAME", ""),
        "MQTT_PASSWORD": os.getenv("MQTT_PASSWORD", ""),
        "MQTT_KEEPALIVE": _int_from_env(
            "MQTT_KEEPALIVE", MQTT_DEFAULT_KEEPALIVE
        ),
    }


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

    mqtt_config_info_str = os.getenv("MQTT_CONFIG_INFO", "{}")
    try:
        mqtt_config_info = json.loads(mqtt_config_info_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"{my_name}: MQTT_CONFIG_INFO environment variable is not valid JSON"
            f"\n\t{mqtt_config_info_str}"
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        ) from exc

    if not isinstance(mqtt_config_info, dict):
        raise ValueError(
            f"{my_name}: MQTT_CONFIG_INFO must decode to a JSON object"
        )

    # Update MQTT_CONFIG with values from environment variables
    for key, config in BROKER_CONFIG.items():
        if key not in mqtt_config_info:
            continue

        secret_cfg = mqtt_config_info[key]
        if not isinstance(secret_cfg, dict):
            continue

        config["MQTT_USERNAME"] = secret_cfg.get(
            "MQTT_USERNAME", config["MQTT_USERNAME"]
        )
        config["MQTT_PASSWORD"] = secret_cfg.get(
            "MQTT_PASSWORD", config["MQTT_PASSWORD"]
        )

    #
    # Update BROKER_NAME from environment variable
    #

    broker_name = os.getenv("BROKER_NAME", DEFAULT_BROKER_NAME)

    broker_aliases = {
        "eclipse": "mqtt.eclipse.org",
        "mqtt-org": "mqtt.eclipse.org",
        "pi2": "PI2",
        "ts-pi2": "TS-PI2",
    }
    broker_key = broker_aliases.get(broker_name, broker_name)
    broker_config = BROKER_CONFIG.get(broker_key)

    if broker_config is None:
        broker_config = _build_env_fallback_config()
        if broker_config is None:
            raise ValueError(
                f"{my_name}: Unknown BROKER_NAME='{broker_name}' and no MQTT_BROKER_ADDRESS provided"
            )

        print(
            f"{my_name}: BROKER_NAME '{broker_name}' not found. "
            "Using MQTT_* environment variables instead."
        )

    print(f"{my_name}: Using broker {broker_name}")
    print(f"\t{broker_config}")
    print(f"\t... which is of type {type(broker_config)}")

    return broker_config
