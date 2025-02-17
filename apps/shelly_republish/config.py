"""
Shelly application-specific configuration.
"""

from typing import Any, Dict

from src.utils.config import load_broker_config

#! Needs Review

# Application-specific settings
DEVICE_TYPES = ["plug-s", "plug"]
UPDATE_TIMEOUT = 300  # seconds
COMMAND_TIMEOUT = 5  # seconds

# Topic patterns
TOPICS = {
    "status": "shellies/+/status",
    "command": "shellies/+/command",
    "response": "shellies/+/response",
}


def get_app_config() -> Dict[str, Any]:
    """Get complete application configuration."""
    broker_config = load_broker_config("BROKER_NAME")

    return {
        "broker": broker_config,
        "device_types": DEVICE_TYPES,
        "update_timeout": UPDATE_TIMEOUT,
        "command_timeout": COMMAND_TIMEOUT,
        "topics": TOPICS,
    }
    }
