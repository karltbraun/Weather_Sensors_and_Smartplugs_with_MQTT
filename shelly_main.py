"""
shelly_main.py 20241116
"""

import logging
import time
from queue import Queue

from config.broker_config import load_broker_config
from src.managers.message_manager_shelly import MessageManager
from src.managers.mqtt_manager import MQTTManager
from src.utils.ktb_logger import ktb_logger
from src.utils.misc_utils import (
    get_pub_root,
    get_pub_source,
    get_sub_topics,
)

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

    logger = ktb_logger(
        clear_logger=True,
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        file_handler="logs/shelly.log",
    )

    # ############################ MQTT Setup ############################ #

    # load in broker information
    broker_config: dict = load_broker_config()
    broker_name = broker_config["MQTT_BROKER_ADDRESS"]

    # MQTT Topic(s)
    sub_topics: list = get_sub_topics("SUB_TOPICS_SHELLY")
    pub_topic_root = get_pub_root()
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

    emsg = (
        f"\n#########################################################################\n"
        f"          Starting up with the following configuration:\n"
        f"  Broker: {broker_name}\n"
        f"  Source: {pub_source}\n"
        f"  Topic Root: {pub_topic_root}\n"
        f"  Subscription Topics: {sub_topics}\n"
        f"  Console log level: {logging.getLevelName(logging.DEBUG)}\n"
        f"  File log level: {logging.getLevelName(logging.DEBUG)}\n"
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

            # ################## publish all updated devices  ################### #

            while not message_queue_out.empty():
                # empty the output queue and publish the updated devices
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
