"""
Configuration utility module for MQTT brokers.
Loads broker configurations and handles credentials from environment.
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

DEFAULT_MQTT_PORT = 1883


@dataclass
class BrokerConfig:
    """MQTT Broker configuration"""

    address: str
    port: int
    keepalive: int = 60
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None


def load_broker_config(broker_name: str) -> BrokerConfig:
    """
    Load broker configuration and credentials.

    Args:
        broker_name: Name of the broker to configure

    Returns:
        BrokerConfig with broker settings and optional credentials

    Raises:
        ValueError: If broker configuration is not found
    """
    load_dotenv()
    logger = logging.getLogger(__name__)

    # we will use the lower case version of the broker name
    broker_name_l = broker_name.lower()
    logger.debug(
        f"Loading broker configuration for {broker_name} -> {broker_name_l}"
    )

    default_broker = {
        "address": f"{broker_name_l}",
        "port": DEFAULT_MQTT_PORT,
        "keepalive": 60,
    }

    # default values if nothing in config
    broker = default_broker
    username = None
    password = None

    # Load broker basic configurations
    config_path = (
        Path(__file__).parent.parent.parent / "config" / "brokers.json"
    )
    if config_path.exists():
        with open(config_path) as f:
            brokers: Dict[str, Dict[str, Any]] = json.load(f)

        if broker_name_l in brokers:
            broker = brokers[broker_name_l]
        else:
            logger.warning(
                "Broker not found in broker config"
                "\n\tUsing default configuration"
            )
    else:
        logger.warning(
            "Broker configuration file not found"
            "\n\tUsing default configuration"
        )

    # Get credentials from MQTT_CONFIG_INFO if available
    mqtt_config_info_str = os.getenv("MQTT_CONFIG_INFO")
    if mqtt_config_info_str:
        try:
            mqtt_config_info = json.loads(mqtt_config_info_str)
            if broker_name_l in mqtt_config_info:
                creds = mqtt_config_info[broker_name_l]
                username = creds.get("MQTT_USERNAME")
                password = creds.get("MQTT_PASSWORD")
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse MQTT_CONFIG_INFO: {e}")

    broker_config = BrokerConfig(
        address=broker["address"],
        port=broker["port"],
        keepalive=broker.get("keepalive", 60),
        username=username,
        password=password,
    )

    logger.debug(
        "Broker configuration:\n"
        "\tAddress: %s\n"
        "\tPort: %s\n"
        "\tKeepalive: %s\n"
        "\tUsername: %s",
        broker_config.address,
        broker_config.port,
        broker_config.keepalive,
        "set" if broker_config.username else "not set",
    )
    return broker_config
