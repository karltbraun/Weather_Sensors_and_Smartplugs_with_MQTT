"""
Weather Sensors application-specific configuration.
"""

import logging
from typing import Any, Dict

from src.utils.config import load_broker_config

# Application-specific settings
logger = logging.getLogger(__name__)
SENSOR_TYPES = ["rtl433", "acurite", "oregon"]
UPDATE_INTERVAL = 60  # seconds

# Topic patterns for this application
TOPICS = {
    "raw_data": "{pub_root}/+/sensors/raw/#",
    "processed_data": "{pub_root}/+/sensors/processed/#",
}

# Processing settings
MAX_QUEUE_SIZE = 1000
BATCH_SIZE = 50


def get_app_config() -> Dict[str, Any]:
    """Get complete application configuration."""
    broker_config = load_broker_config("BROKER_NAME")

    app_config = {
        "\nbroker": broker_config,
        "\nsensor_types": SENSOR_TYPES,
        "\nupdate_interval": UPDATE_INTERVAL,
        "\ntopics": TOPICS,
        "\nmax_queue_size": MAX_QUEUE_SIZE,
        "\nbatch_size": BATCH_SIZE,
    }

    logger.info(
        "\n****************************************************************************************"
        "\nbroker: %s"
        "\nsensor_types: %s"
        "\nupdate_interval: %s"
        "\ntopics: %s"
        "\nmax_queue_size: %s"
        "\nbatch_size: %s"
        "\n****************************************************************************************",
        broker_config,
        SENSOR_TYPES,
        UPDATE_INTERVAL,
        TOPICS,
        MAX_QUEUE_SIZE,
        BATCH_SIZE,
    )

    return app_config
