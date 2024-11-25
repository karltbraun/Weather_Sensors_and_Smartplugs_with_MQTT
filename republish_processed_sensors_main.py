"""
republish_processed_sensors_main.py - 20241119

main entry point for the code to consume flat MQTT messages about sensors and
republish them as devices with json payloads.

This script subscribes to raw sensor data from an MQTT broker.
The raw data consists of attributes published in their own subtopics for each device,
e.g., KTBMES/raw/1234/temperature_C, KTBMES/raw/1234/channel, KTBMES/raw/1234/noise, etc.

The script collects attributes for each device (identified by device ID) and stores them
in a dictionary indexed by the device ID. The value includes the time the data was last
received, the protocol_id (which indicates how to parse the rest of the data),
and the rest of the data as a sub-dictionary.

Periodically, the dictionary of devices is written to a JSON file for further use.
At startup, if the JSON file exists, it initializes the dictionary with the data from the file.

The script handles known temperature sensors and other discovered devices, analyzing their data
for potential use. The JSON file can be used to either republish the data to a new topic or
display it on a web page.
"""

import logging
import time
from datetime import datetime
from queue import Queue
from typing import Any, Dict

from dotenv import load_dotenv

# describes mqtt broker parameters like host address, port, etc.
from config.broker_config import BROKER_CONFIG, load_broker_config

# transforms input data into device attributes
from src.managers.message_manager_republish import MessageManager

# handles all MQTT specific functions
from src.managers.mqtt_manager import MQTTManager

# handles all RTL-433 protocol specific functions
from src.managers.protocol_manager import ProtocolManager

# maps device IDs to known sensor names
from src.utils.device_maps import my_sensors_id_map

# custom logger
from src.utils.logger_setup import logger_setup

# utility functions
from src.utils.misc_utils import (  # get_pub_root,
    get_logging_levels,
    get_pub_root,
    get_pub_source,
    get_sub_topics,
)

# ###################################################################### #
#                        Global Variables and Constants
# ###################################################################### #

# Define the devices dictionary at the module level
protocol_manager = ProtocolManager()


# ###################################################################### #
#     setup logger, load broker configurations, load env variables       #
# ###################################################################### #

load_dotenv()
logging_levels: dict = get_logging_levels()

logger = logger_setup(
    clear_logger=logging_levels["clear"],
    console_level=logging_levels["console"],
    file_level=logging_levels["file"],
    file_handler="logs/republish_processed_sensors.log",
)

load_dotenv()
load_broker_config()


# ###################################################################### #
#                             get_protocol_id
# ###################################################################### #


def get_protocol_id(device_data: dict) -> str:
    """
    Get the protocol ID from the device data.
    """
    my_name = "get_protocol_id"
    protocol_id = device_data.get("protocol_id", None)

    if not isinstance(protocol_id, str):
        raise ValueError(
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"{my_name}: protocol_id is not a string: \n"
            f"\tDevice ID: {device_data['device_id']}\n"
            f"\tDevice Name: {device_data['device_name']}\n"
            f"\tProtocol_id: {protocol_id}\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        )

    if protocol_id is None or not isinstance(protocol_id, str):
        raise ValueError(
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"{my_name}: bad protocol_id: \n"
            f"\tDevice ID: {device_data['device_id']}\n"
            "\tDevice Name: {device_data['device_name']}\n"
            "\tProtocol_id: {protocol_id}\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        )
    return protocol_id


# ###################################################################### #
#                             get_topic_for_device
# ###################################################################### #


def get_topic_for_device(
    device_id: str, device_data: Dict[str, Any], pub_topics: Dict[str, str]
) -> str:
    """
    Get the topic for the device based on the protocol ID.
    """
    # my_name = "get_topic_for_device"

    topic_root: str = pub_topics["pub_topic_base"]
    if device_id in my_sensors_id_map:
        # if device ID is one of my devices publish to the ktbmes sensor topic
        topic_root: str = pub_topics["pub_topic_base"]
        topic: str = f"{topic_root}/house_weather_sensors/{device_data['device_name']}"

    else:
        protocol_id: str = get_protocol_id(device_data)

        # lmsg = (
        #     "\n...............................................................\n"
        #     "get_topic_for_device: checking protocol id\n"
        #     f"\tDevice ID: {device_id}\n"
        #     f"\tDevice Name: {device_data['device_name']}\n"
        #     f"\tProtocol ID: {protocol_id}\n"
        #     f"\tProtocol ID Type: {type(protocol_id)}\n"
        #     f"\tis_weather_sensor: {protocol_manager.is_weather_sensor(protocol_id)}\n"
        #     f"\tis_pressure_sensor: {protocol_manager.is_pressure_sensor(protocol_id)}\n"
        #     "...............................................................\n"
        # )
        # logging.debug(lmsg)

        if protocol_manager.is_weather_sensor(protocol_id):
            topic_base = f"{topic_root}/other_weather_sensorsi"
        elif protocol_manager.is_pressure_sensor(protocol_id):
            topic_base = f"{topic_root}/other_pressure_sensors"
        else:
            topic_base = f"{topic_root}/unknown_other_sensors"
            lmsg = (
                "\n...............................................................\n"
                "get_topic_for_device: Unknown device type\n"
                f"\tDevice ID: {device_id}\n"
                f"\tDevice Name: {device_data['device_name']}\n"
                f"\tProtocol ID: {protocol_id}\n"
                "...............................................................\n"
            )
            logging.debug(lmsg)

        topic = f"{topic_base}/{device_data['device_name']}"

    return topic


# ###################################################################### #
#                             publish_device
# ###################################################################### #


def publish_device(
    device_id: int,
    device_data: dict,
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
    time_now = datetime.now().timestamp()

    # publish and update published times
    mqtt_manager.publish_dict(topic, device_data)
    device_data["time_last_published_ts"] = time_now
    device_data["time_last_published_iso"] = datetime.fromtimestamp(
        time_now
    ).isoformat()

    logging.debug(
        "%s: Updated last published time for device %s\n"
        "\ttime_last_published_ts: %s\n"
        "\ttime_last_published_iso: %s\n",
        my_name,
        device_id,
        device_data["time_last_published_ts"],
        device_data["time_last_published_iso"],
    )


# ###################################################################### #
#                             device_not_updated
# ###################################################################### #


def device_updated(device_data: dict) -> bool:
    """
    Check if the device has been updated since it was last seen.
    """
    my_name = "device_updated"

    updated = False
    last_seen = device_data.get("time_last_seen_ts", 0)
    last_published = device_data.get("time_last_published_ts", 0)

    if last_seen is None or last_published is None:
        logging.debug(
            "%s: last_seen or last_published is None:\n", my_name
        )
    elif last_seen > last_published:
        updated = True

    return updated


# ###################################################################### #
#                       generate_pub_topics
# ###################################################################### #


def generate_pub_topics(pub_source: str) -> dict:
    """Generate a dictionary of publication topics based on the source."""
    pub_root = get_pub_root()
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
    BROKER_NAME = "TS-VULTR1"  # pylint: disable=invalid-name
    SLEEP_TIME_S = 5  # pylint: disable=invalid-name

    # MQTT Topic(s)
    sub_topics: list = get_sub_topics("SUB_TOPICS_REPUBLISH")
    pub_source = get_pub_source()
    pub_topics = generate_pub_topics(pub_source)

    # ############################ MQTT Setup ############################ #

    broker_name = BROKER_NAME
    mqtt_manager = MQTTManager(
        broker_config=BROKER_CONFIG[broker_name],
        subscribe_topics=sub_topics,
        publish_topic_root=pub_topics["pub_topic_base"],
    )
    message_queue: Queue = mqtt_manager.message_queue_in
    client = mqtt_manager.client

    # ###################  message processing setup   ####################### #

    message_manager = MessageManager()
    devices = message_manager.devices

    # #########################  display banner  ####################### #

    emsg = (
        f"\n#########################################################################\n"
        f"          Starting up with the following configuration:\n"
        f"  Broker: {broker_name}\n"
        f"  Source: {pub_source}\n"
        f"  PUB_TOPICS:\n"
        f"    {pub_topics}\n"
        f"  Subscription Topics: {sub_topics}\n"
        f"  Console log level: {logging_levels["console"]}\n"
        f"  File log level: {logging_levels["file"]}\n"
        f"#########################################################################\n"
    )
    logger.info(emsg)

    time.sleep(5)  # pause to read output from logging

    # #########################  Main Loop  ####################### #
    #
    # Process any messages put in the queue from the on_message routine
    # Give up the CPU for a while then check again
    #

    logger.debug("Main: Starting MQTT loop\n")
    client.loop_start()

    try:
        while True:
            # the on_message callback, which is asynchronous, puts messages in the queue
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
                    message_queue.get(), devices, protocol_manager
                )

            # ################## publish all updated devices  ################### #

            logging.debug(
                "Main: Loop: Processing %d devices", len(devices)
            )
            for device_id, device_data in devices.items():
                if device_updated(device_data):
                    topic: str = get_topic_for_device(
                        device_id, device_data, pub_topics
                    )
                    publish_device(
                        device_id, device_data, topic, mqtt_manager
                    )

    except KeyboardInterrupt:
        print("Keyboard Interrupt received, exiting.")
    finally:
        print("Disconnecting from MQTT broker.")
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
