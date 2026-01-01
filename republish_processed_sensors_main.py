"""republish_processed_sensors_main.py - Main entry point for RTL-433 sensor data processing.

This script processes raw sensor data from RTL-433 received via MQTT and republishes it
as structured JSON payloads organized by device. It supports dynamic configuration updates
via MQTT for managing local sensor definitions.

Data Flow:
    1. Subscribes to raw sensor topics with individual attributes per subtopic
       (e.g., <root>/raw/<device_id>/temperature_C, <root>/raw/<device_id>/humidity)
    2. Aggregates attributes by device ID into unified device records
    3. Enriches data with protocol information and local sensor metadata
    4. Republishes as JSON payloads to device-specific topics
    5. Persists device data to JSON file for analysis and web display

Configuration:
    - Loads broker settings from config/broker_config.py
    - Manages local sensor definitions via LocalSensorManager
    - Supports MQTT-based config updates on <root>/sensors/config/local_sensors
    - Publishes current config to <root>/<host>/sensors/config/local_sensors
    - Uses environment variables for topic roots, logging, and behavior settings

Key Features:
    - Automatic protocol identification via RTL-433 protocol IDs
    - Device registry with last-seen timestamps and publish tracking
    - Periodic data persistence with configurable intervals
    - Temperature conversion (Celsius to Fahrenheit)
    - MQTT broker accessibility checking before startup
    - Dynamic configuration reload without restart

Environment Variables:
    PUB_SOURCE: Publishing host identifier (default: hostname)
    PUB_TOPIC_ROOT: Root topic for publishing (required)
    SUB_TOPICS_SENSORS: Comma-separated subscription topics
    CONSOLE_LOG_LEVEL: Console logging level (default: DEBUG)
    FILE_LOG_LEVEL: File logging level (default: DEBUG)
    CLEAR_LOG_FILE: Clear log file on startup (default: True)
    PUBLISH_INTERVAL_MAX: Maximum seconds between republishing (default: 300)
    CONFIG_SUBSCRIBE_TIMEOUT: Seconds to wait for config messages (default: 10)

Usage:
    python republish_processed_sensors_main.py

Author: ktb
Date: 2024-08-23
Updated: 2024-12-30
"""


# ###################################################################### #
#                             Import Libraries
# ###################################################################### #

import json
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
from src.utils.misc_utils import (
    get_config_subscribe_timeout,
    get_logging_levels,  # get_pub_topic_root,
    get_pub_source,
    get_pub_topic_root,
    get_publish_interval_max,
    get_sub_topics,
)

# MQTT broker accessibility check utility
from src.utils.mqtt_broker_check import check_mqtt_broker_accessibility

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
if not broker_config:
    raise ValueError(
        "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        "\tload_broker_config returns <None>"
        "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
    )
BROKER_ADDRESS = broker_config["MQTT_BROKER_ADDRESS"]
BROKER_PORT = broker_config.get("MQTT_BROKER_PORT", 1883)
print(
    "#######################################################################"
)
print(f"BROKER_ADDRESS: {BROKER_ADDRESS}")
print(
    "#######################################################################"
)

# Check MQTT broker accessibility before proceeding
if not check_mqtt_broker_accessibility(BROKER_ADDRESS, BROKER_PORT):
    logger.error(
        f"MQTT broker {BROKER_ADDRESS}:{BROKER_PORT} is not accessible. Exiting."
    )
    exit(1)


# Helper to publish local sensors config to MQTT
def publish_local_sensors_config(mqtt_client, config_data, topic):
    """
    Publish local sensors configuration to MQTT.

    Args:
        mqtt_client: MQTT client instance
        config_data: Sensor configuration data to publish
        topic: MQTT topic to publish to
    """
    payload = json.dumps(config_data)
    mqtt_client.publish(topic, payload, retain=True)
    logger.info(f"Published local sensors config to {topic} (retain=True)")


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

    # Load MQTT topic configuration from environment
    pub_source = get_pub_source()
    pub_root = get_pub_topic_root()

    mqtt_topics = {
        "canonical": os.getenv(
            "MQTT_TOPIC_LOCAL_SENSORS",
            f"{pub_root}/sensors/config/local_sensors",
        ),  # Canonical source - all services subscribe to this
        "host_specific": f"{pub_root}/{pub_source}/sensors/config/local_sensors",  # Host-specific publish topic
    }

    config_subscribe_timeout = get_config_subscribe_timeout()

    # MQTT Topic(s)
    sub_topics: list = get_sub_topics("SUB_TOPICS_REPUBLISH")

    # Add canonical config topic to subscription list
    if mqtt_topics["canonical"] not in sub_topics:
        sub_topics.append(mqtt_topics["canonical"])
        logger.info(
            f"Added canonical config topic to subscriptions: {mqtt_topics['canonical']}"
        )

    # pub_source already retrieved above for topic construction
    pub_topics = generate_pub_topics(pub_source)

    # ############################ MQTT Setup ############################ #

    broker_address: str = BROKER_ADDRESS
    mqtt_manager = MQTTManager(
        broker_config=broker_config,
        subscribe_topics=sub_topics,
        publish_topic_root=pub_topics["pub_topic_base"],
    )
    message_queue: Queue = mqtt_manager.message_queue_in
    client = mqtt_manager.client

    # ###################  message processing setup   ####################### #

    # Ensure Device class uses the correct LocalSensorManager
    from src.managers.device_manager import Device

    Device.local_sensor_manager = local_sensor_manager

    message_manager = MessageManager(
        local_sensor_manager,
        config_update_topic=mqtt_topics["canonical"],
        config_current_topic=None,  # No longer using separate current topic
    )
    device_registry: DeviceRegistry = DeviceRegistry()
    message_manager.device_registry = device_registry

    # Publish initial local_sensors config on startup (with host in path)
    publish_local_sensors_config(
        client, local_sensor_manager.sensors, mqtt_topics["host_specific"]
    )

    # #########################  display banner  ####################### #

    logger.info(
        "\n#########################################################################\n"
        "          Starting up at %s with the following configuration:\n"
        "  Version: 2025-12-30 (with updated config topic structure)\n"
        "  Broker: %s\n"
        "  Source: %s\n"
        "  PUB_TOPICS:\n"
        "    %s\n"
        "  Subscription Topics: %s\n"
        "  Config Update Topic: %s\n"
        "  Config Current Global Topic: %s\n"
        "  Config Current Host Topic: %s\n"
        "  Config Subscribe Timeout: %d seconds\n"
        "  Local Sensors: %d configured\n"
        "  Console log level: %s\n"
        "  File log level: %s\n"
        "#########################################################################\n",
        datetime.now().isoformat(),
        broker_address,
        pub_source,
        pub_topics,
        sub_topics,
        mqtt_topics["canonical"],
        mqtt_topics["host_specific"],
        config_subscribe_timeout,
        local_sensor_manager.get_sensor_count(),
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

    # Check for retained config message on startup
    # Subscribe to global 'current' topic to get retained message only
    logger.info(
        f"Checking for retained config on MQTT canonical topic: {mqtt_topics['canonical']}..."
    )
    client.subscribe(mqtt_topics["canonical"])

    # Wait for retained message with timeout
    config_loaded_from_mqtt = False
    start_time = time.time()

    while (time.time() - start_time) < config_subscribe_timeout:
        if not message_queue.empty():
            msg = message_queue.get()
            if msg.topic == mqtt_topics["canonical"]:
                # Found config message on global current topic
                try:
                    if isinstance(msg.payload, bytes):
                        payload = msg.payload.decode("utf-8")
                    else:
                        payload = msg.payload
                    config_data = json.loads(payload)

                    # Validate and use the MQTT config
                    is_valid, validation_msg = (
                        local_sensor_manager.validate_sensor_data(
                            config_data
                        )
                    )
                    if is_valid:
                        local_sensor_manager.sensors = config_data
                        logger.info(
                            f"Loaded {len(local_sensor_manager.sensors)} sensors from MQTT retained message"
                        )
                        config_loaded_from_mqtt = True
                        # Republish to host-specific topic
                        publish_local_sensors_config(
                            client,
                            local_sensor_manager.sensors,
                            mqtt_topics["host_specific"],
                        )
                        break  # Exit loop, we got what we needed
                    else:
                        logger.warning(
                            f"MQTT config validation failed: {validation_msg}, using file config"
                        )
                        break
                except Exception as e:
                    logger.warning(
                        f"Failed to load config from MQTT retained message: {e}, using file config"
                    )
                    break
            else:
                # Put non-config messages back in queue for processing
                message_queue.put(msg)
        else:
            # Queue empty, sleep briefly and check again
            time.sleep(0.1)

    # Note: We stay subscribed to canonical topic to receive future updates
    # No unsubscribe needed as we want ongoing updates
    logger.info(
        f"Continuing to monitor {mqtt_topics['canonical']} for configuration updates"
    )

    if not config_loaded_from_mqtt:
        elapsed = time.time() - start_time
        logger.info(
            f"No retained MQTT config found after {elapsed:.1f}s, using file config"
        )

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
                msg = message_queue.get()
                # Process message (includes config update handling)
                result = message_manager.process_message(
                    msg, protocol_manager
                )

                # If config was updated, publish the new config
                if result and result.get("config_updated"):
                    # Refresh device names for all devices after config update
                    for (
                        device_id,
                        device,
                    ) in device_registry.devices.items():
                        device.device_name_from_id_set(device_id)
                    # Publish to host-specific topic
                    publish_local_sensors_config(
                        client,
                        local_sensor_manager.sensors,
                        mqtt_topics["host_specific"],
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

                # need to check for protocol id 55 and publish to special topic if so.
                protocols_to_track: list = ["55", "91"]
                if (
                    proto_id := device_data.protocol_id()
                ) in protocols_to_track:
                    topic: str = pub_topics["unknown_TPM_sensors"]
                    topic: str = f"KTBMES/{pub_source}/sensors/proto_{proto_id}/{device_data.device_name()}"
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
