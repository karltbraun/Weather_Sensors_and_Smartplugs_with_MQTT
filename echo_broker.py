"""echo_broker.py - Diagnostic tool for MQTT broker connectivity and message flow.

This script is a testing/diagnostic utility that echoes MQTT messages back to the broker.
It subscribes to specified topics, logs all received messages, and optionally republishes
them to help verify broker connectivity and message flow.

Key Features:
    - Subscribe to any MQTT topic pattern
    - Echo received messages to console with detailed logging
    - Optionally republish messages to test topics
    - Broker connection diagnostics
    - Message queue monitoring

Environment Variables:
    PUB_SOURCE: Publishing host identifier (default: hostname)
    PUB_TOPIC_ROOT: Root topic for publishing (required)
    SUB_TOPICS_REPUBLISH: Comma-separated subscription topics
    CONSOLE_LOG_LEVEL: Console logging level (default: DEBUG)
    FILE_LOG_LEVEL: File logging level (default: DEBUG)

Usage:
    python echo_broker.py

Author: ktb
Date: 2024-11-19
Updated: 2024-12-31
"""


# ###################################################################### #
#                             Import Libraries
# ###################################################################### #

import logging
import os
import time
from datetime import datetime

# from datetime import datetime
from queue import Queue
from typing import Dict

from dotenv import load_dotenv

# describes mqtt broker parameters like host address, port, etc.
from config.broker_config import BROKER_CONFIG, load_broker_config

# handles output file
from src.managers.data_repository_manager import DataRepositoryManager

# handles all device specific functions (sensors)
from src.managers.device_manager import (
    Device,
    DeviceRegistry,
    LocalSensorManager,
)

# transforms input data into device attributes
from src.managers.message_manager_republish import MessageManager

# handles all MQTT specific functions
from src.managers.mqtt_manager import MQTTManager

# handles all RTL-433 protocol specific functions
from src.managers.protocol_manager import ProtocolManager

# custom logger
from src.utils.logger_setup import logger_setup

# utility functions
from src.utils.misc_utils import (  # get_pub_topic_root,
    get_logging_levels,
    get_pub_source,
    get_pub_topic_root,
    get_publish_interval_max,
    get_sub_topics,
)

# ###################################################################### #
#                        Global Variables and Constants
# ###################################################################### #

# manages all RTL_433 protocols related functions
protocol_manager = ProtocolManager()

# manages all local sensor related functions
#   mainly identifies those sensors which are local to us
#   vs others which RTL_433 has sees in the area
local_sensor_manager = LocalSensorManager(
    config_dir="./config",
    sensors_file="local_sensors.json",
    check_interval=60,
)

data_repository_manager = DataRepositoryManager(
    "data", "device_data.json", 60
)

# ###################################################################### #
#     setup logger, load broker configurations, load env variables       #
# ###################################################################### #

load_dotenv()
logging_levels: dict = get_logging_levels()
PUBLISH_INTERVAL_MAX_S = get_publish_interval_max()


logger = logger_setup(
    clear_logger=logging_levels["clear"],
    console_level=logging_levels["console"],
    file_level=logging_levels["file"],
    file_handler="logs/republish_processed_sensors.log",
)

# Load broker configuration
broker_config = load_broker_config()
BROKER_ADDRESS = broker_config["MQTT_BROKER_ADDRESS"]
print(
    "#######################################################################"
)
print(f"BROKER_ADDRESS: {BROKER_ADDRESS}")
print(
    "#######################################################################"
)


# ###################################################################### #
#                             get_topic_for_device
# ###################################################################### #


def get_topic_for_device(
    device_id: str, device_data: Device, pub_topics: Dict[str, str]
) -> str:
    """
    Get the topic for the device based on the protocol ID.
    """
    # my_name = "get_topic_for_device"

    topic_root: str = pub_topics["pub_topic_base"]
    if local_sensor_manager.is_local_sensor(device_id):
        # if device ID is one of my devices publish to the ktbmes sensor topic
        topic_root: str = pub_topics["pub_topic_base"]
        topic: str = f"{topic_root}/house_weather_sensors/{device_data.device_name()}"

    else:
        # protocol_id: str = get_protocol_id(device_data)
        protocol_id: str = device_data.protocol_id()

        if protocol_manager.is_weather_sensor(protocol_id):
            topic_base = f"{topic_root}/other_weather_sensors"
        elif protocol_manager.is_pressure_sensor(protocol_id):
            topic_base = f"{topic_root}/other_pressure_sensors"
        else:
            topic_base = f"{topic_root}/unknown_other_sensors"
            logging.debug(
                "\n...............................................................\n"
                "get_topic_for_device: Unknown device type\n"
                "\tDevice ID: %s\n"
                "\tDevice Name: %s\n"
                "\tProtocol ID: %s\n"
                "...............................................................\n",
                device_id,
                device_data.device_name(),
                protocol_id,
            )

        topic = f"{topic_base}/{device_data.device_name()}"

    return topic


# ###################################################################### #
#                             publish_device
# ###################################################################### #


def publish_device(
    device_id: int,
    device_data: Device,
    topic: str,
    mqtt_manager: MQTTManager,
) -> None:
    """Publish the device data"""
    my_name = "publish_device"

    logging.debug(
        "%s: Publishing to known sensor topic:\n"
        "\tTopic: %s\n"
        "\tDevice ID: %s\n"
        "\tDevice Data: %s\n",
        my_name,
        topic,
        device_id,
        device_data,
    )

    # get the current time (for updating time published) before we actually
    # publish in case new data comes in while we are processing

    # publish and update published times
    #   need to set the last published time before publishing
    #   so it is set for the first time published.
    device_data.last_last_published_now_set()
    mqtt_manager.publish_dict(topic, device_data.device)

    logging.debug(
        "%s: Updated last published time for device %s\n"
        "\ttime_last_published_ts: %s\n"
        "\ttime_last_published_iso: %s\n",
        my_name,
        device_id,
        device_data.time_last_seen_ts(),
        device_data.time_last_seen_iso(),
    )


# ###################################################################### #
#                       generate_pub_topics
# ###################################################################### #


def generate_pub_topics(pub_source: str) -> dict:
    """Generate a dictionary of publication topics based on the source."""
    pub_root = get_pub_topic_root()
    pub_topic_base = f"{pub_root}/{pub_source}/sensors"
    return {
        "pub_topic_base": pub_topic_base,
        "my_weather_sensors": f"{pub_topic_base}/ktb_sensors",
        "unknown_weather_sensors": f"{pub_topic_base}/unknown_weather_sensors",
        "unknown_other_sensors": f"{pub_topic_base}/unknown_other_sensors",
        "unknown_TPM_sensors": f"{pub_topic_base}/unknown_TPM_sensors",
    }


# ###################################################################### #
#                             Main Function
# ###################################################################### #


def main() -> None:
    """
    Main function to set up and run the MQTT client for processing messages.
    """
    # function constants

    SLEEP_TIME_S = 5  # pylint: disable=invalid-name

    # MQTT Topic(s)
    sub_topics: list = ["KTBMES/raw/#"]
    pub_source = get_pub_source()
    pub_topics = generate_pub_topics(pub_source)

    # ############################ MQTT Setup ############################ #

    broker_address = BROKER_ADDRESS
    mqtt_manager = MQTTManager(
        broker_config=broker_config,
        subscribe_topics=sub_topics,
        publish_topic_root=pub_topics["pub_topic_base"],
    )
    message_queue: Queue = mqtt_manager.message_queue_in
    client = mqtt_manager.client

    # ###################  message processing setup   ####################### #

    message_manager = MessageManager(local_sensor_manager)
    device_registry: DeviceRegistry = DeviceRegistry()
    message_manager.device_registry = device_registry

    # #########################  display banner  ####################### #

    logger.info(
        "\n#########################################################################\n"
        "          Starting up at %s with the following configuration:\n"
        "  Version: 2024-12-18T0654\n"
        "  Broker: %s\n"
        "  Source: %s\n"
        "  PUB_TOPICS:\n"
        "    %s\n"
        "  Subscription Topics: %s\n"
        "  Console log level: %s\n"
        "  File log level: %s\n"
        "#########################################################################\n",
        datetime.now().isoformat(),
        broker_address,
        pub_source,
        pub_topics,
        sub_topics,
        logging_levels["console"],
        logging_levels["file"],
    )

    time.sleep(5)  # pause to read output from logging

    # ##################################  Main Loop  ################################ #
    #
    # Process any messages put in the queue from the on_message routine
    # Give up the CPU for a while then check again
    #

    logger.debug("Main: Starting MQTT loop\n")
    client.loop_start()

    try:
        while True:
            # the on_message callback, which is asynchronous, puts messages in the queue.
            # process_message_queue empties the queue and updates items in the device registry
            # (devices) with the new data

            if message_queue.empty():
                # If the queue is empty, pause
                logging.debug(
                    "Main: Loop:\n\tQueue is empty. Sleeping for %d seconds...\n",
                    SLEEP_TIME_S,
                )
                time.sleep(SLEEP_TIME_S)
                continue

            # since there are messages in the queue, process them
            #   processing involves updating DeviceRegistry with new data
            while not message_queue.empty():
                logging.debug(
                    "Main: Loop: Processing %d messages",
                    message_queue.qsize(),
                )
                message_manager.process_message(
                    message_queue.get(), protocol_manager
                )

            # ################## publish all updated devices  ################### #

            logging.debug(
                "Main: Loop: Processing %d devices",
                len(device_registry.devices),
            )

            current_time = time.time()

            for device_id, device_data in device_registry.devices.items():
                if (
                    device_data.device_updated()
                    or device_data.publish_interval_max_exceeded(
                        current_time, PUBLISH_INTERVAL_MAX_S
                    )
                ):
                    topic: str = get_topic_for_device(
                        device_id, device_data, pub_topics
                    )
                    publish_device(
                        device_id, device_data, topic, mqtt_manager
                    )

            # ################## dump data to file  ################### #

            data_repository_manager.dump_data(
                device_registry.devices,
                data_repository_manager.dump_file_path,
            )

    except KeyboardInterrupt:
        print("Keyboard Interrupt received, exiting.")
    finally:
        print("Disconnecting from MQTT broker.")
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
