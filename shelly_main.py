"""shelly_main.py - MQTT processor for Shelly smart plug data.

This script processes MQTT messages from Shelly smart plugs and republishes them
in a standardized format with device metadata and room associations.

Data Flow:
    1. Subscribes to Shelly device topics (configured via SUB_TOPICS_SHELLY env var)
    2. Processes incoming JSON messages with device status and power readings
    3. Flattens nested JSON structures into individual attributes
    4. Creates structured publication topics: <root>/<host>/<room>/smartplugs/<device>/<tag>
    5. Publishes individual attributes to their respective topics

Configuration:
    - Loads broker settings from config/broker_config.py
    - Maps devices to rooms via DEVICE_ROOM_MAP (in message_manager_shelly.py)
    - Uses environment variables for topic configuration and logging

Environment Variables:
    PUB_SOURCE: Publishing host identifier (default: hostname)
    PUB_TOPIC_ROOT: Root topic for publishing (required)
    SUB_TOPICS_SHELLY: Comma-separated Shelly device topics to subscribe to
    CONSOLE_LOG_LEVEL: Console logging level (default: DEBUG)
    FILE_LOG_LEVEL: File logging level (default: DEBUG)
    CLEAR_LOG_FILE: Clear log file on startup (default: True)

Usage:
    python shelly_main.py

Author: ktb
Date: 2024-11-16
Updated: 2024-12-30
"""

import logging
import time
from datetime import datetime
from queue import Queue

from dotenv import load_dotenv

from config.broker_config import load_broker_config
from src.managers.message_manager_shelly import MessageManager
from src.managers.mqtt_manager import MQTTManager
from src.utils.logger_setup import logger_setup
from src.utils.misc_utils import (
    get_logging_levels,
    get_pub_source,
    get_pub_topic_root,
    get_sub_topics,
)

# MQTT broker accessibility check utility
from src.utils.mqtt_broker_check import check_mqtt_broker_accessibility

load_dotenv()

# ###################################################################### #
#                             Main Function
# ###################################################################### #


def main() -> None:
    """
    Main function to set up and run the MQTT client for processing messages.
    """

    # local constants
    SLEEP_TIME_S = 5  # pylint: disable=invalid-name

    # ############################ Logger Setup ############################ #

    logging_levels: dict = get_logging_levels()

    logger = logger_setup(
        clear_logger=logging_levels["clear"],
        console_level=logging_levels["console"],
        file_level=logging_levels["file"],
        file_handler="logs/shelly.log",
    )

    # ############################ MQTT Setup ############################ #

    # load in broker information

    broker_config: dict = load_broker_config()
    print(
        f"*** broker config:\n\ttype: {type(broker_config)}\n\t{broker_config}\n\t{broker_config}"
    )
    broker_address = broker_config["MQTT_BROKER_ADDRESS"]
    broker_port = broker_config.get("MQTT_BROKER_PORT", 1883)

    # Check MQTT broker accessibility before proceeding
    if not check_mqtt_broker_accessibility(broker_address, broker_port):
        logger.error(
            f"MQTT broker {broker_address}:{broker_port} is not accessible. Exiting."
        )
        exit(1)

    # MQTT Topic(s)
    sub_topics: list = get_sub_topics("SUB_TOPICS_SHELLY")
    pub_topic_root = get_pub_topic_root()
    pub_source = get_pub_source()

    # intantiate the MQTT manager
    #  we set the publish_topic_root to NULL because we create it in the message_manager
    mqtt_manager = MQTTManager(
        broker_config=broker_config,
        subscribe_topics=sub_topics,
        publish_topic_root="NULL",
    )

    # instantiate the MQTT client and get the message queues setup
    client = mqtt_manager.client
    # input queue contains mqtt messages from the broker
    message_queue_in: Queue = mqtt_manager.message_queue_in
    # output queue contains tuples of (tag, payload, qos, and retain)
    #   values to be published.  The tag will be the last item in the topic string
    message_queue_out: Queue = mqtt_manager.message_queue_out

    # ###################  message processing setup   ####################### #

    message_manager = MessageManager()

    # #########################  display banner  ####################### #

    logger.info(
        "\n#########################################################################\n"
        "  Starting up at %s with the following configuration:\n"
        "  Version: 20241202T1605\n"
        "  Broker: %s\n"
        "  Source: %s\n"
        "  Topic Root: %s\n"
        "  Subscription Topics: %s\n"
        "  Console log level: %s\n"
        "  File log level: %s\n"
        "#########################################################################\n",
        datetime.now(),
        broker_address,
        pub_source,
        pub_topic_root,
        sub_topics,
        logging_levels["console"],
        logging_levels["file"],
    )

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
            # the on_message callback, which is asynchronous, puts messages in message_queue_in
            # if there are messages in the queue, process them and queue up the results
            # for publishing.
            # We check the queue somewhat redundantly so we can give up the CPU for a while
            # if it is empty

            if message_queue_in.empty():
                # If the queue is empty, pause
                logging.debug(
                    "Main: Loop:\n\tQueue is empty. Sleeping for %d seconds...\n",
                    SLEEP_TIME_S,
                )
                time.sleep(SLEEP_TIME_S)
                continue

            # since there are messages in the queue, process them
            while not message_queue_in.empty():
                # empty the input queue and fill the output queue
                logging.debug(
                    "Main: Loop: Processing %d messages",
                    message_queue_in.qsize(),
                )
                msg = message_queue_in.get()
                message_manager.process_message(msg, message_queue_out)

            #
            # publish all messages in the output queue
            #

            while not message_queue_out.empty():
                pub_topic, payload, qos, retain = message_queue_out.get()
                logging.debug(
                    "Main: Loop: Publishing:\n\tTopic: %s\n\tPayload: %s\n",
                    pub_topic,
                    payload,
                )
                client.publish(
                    pub_topic, payload, qos, retain, properties=None
                )

    except KeyboardInterrupt:
        print("Keyboard Interrupt received, exiting.")
    finally:
        print("Disconnecting from MQTT broker.")
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
