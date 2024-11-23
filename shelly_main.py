"""
shelly_main.py 20241116
"""

import logging
import os
import subprocess
import time
from datetime import datetime
from queue import Queue

from dotenv import load_dotenv

from config.broker_config import BROKER_CONFIG, load_broker_config
from src.managers.aamqtt_manager_shelly import MQTTManager
from src.managers.message_manager_shelly import MessageManager

# from src.managers.protocol_manager import ProtocolManager
# from src.models import devices
# from src.utils.device_maps import my_sensors_id_map
from src.utils.ktb_logger import ktb_logger

load_dotenv()


# ###################################################################### #
#                       normalize_payload                                #
# ###################################################################### #


def normalize_payload(payload: dict) -> dict:
    """
    Normalize the payload based on the topic.
    This is a placeholder function in case we need to do something to
    normalize the payload before further processing.
    """
    # Implement your normalization logic here

    return payload


# ###################################################################### #
#                             get_protocol_id
# ###################################################################### #


def get_protocol_id(device_data: dict) -> int:
    """
    Get the protocol ID from the device data.
    """
    my_name = "get_protocol_id"
    protocol_id = device_data.get("protocol", -1)
    if isinstance(protocol_id, str):
        protocol_id = int(protocol_id)

    if not isinstance(protocol_id, int):
        raise ValueError(
            "***************************************************************"
            f"{my_name}: protocol_id is not an integer: \n"
            f"\tProtocol_id: {protocol_id}"
            "***************************************************************"
        )

    return protocol_id


# ###################################################################### #
#                             publish_device
# ###################################################################### #

# client.publish for reference:
#   client.publish(topic, payload=None, qos=0, retain=False, properties=None)


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

    emsg = (
        f"{my_name}: Updated last published time for deviced {device_id}\n"
        f"\ttime_last_published_ts: {device_data['time_last_published_ts']}\n"
        f"\ttime_last_published_iso: {device_data['time_last_published_iso']}\n"
    )
    logging.debug(emsg)


# ###################################################################### #
#                             device_not_updated
# ###################################################################### #


def device_not_updated(device_data: dict) -> bool:
    """
    Check if the device has been updated since it was last seen.
    """
    my_name = "device_not_updated"

    not_updated = False
    last_seen = device_data.get("time_last_seen_ts", 0)
    last_published = device_data.get("time_last_published_ts", 0)

    if last_seen is None or last_published is None:
        logging.debug(
            "%s: last_seen or last_published is None:\n", my_name
        )
    elif last_seen < last_published:
        not_updated = True

    return not_updated


# ###################################################################### #
#                             Main Function
# ###################################################################### #


def main() -> None:
    """
    Main function to set up and run the MQTT client for processing messages.
    """
    # function constants - set config values here
    load_broker_config()
    BROKER_NAME = "TS-VULTR1"  # pylint: disable=invalid-name
    SLEEP_TIME_S = 5  # pylint: disable=invalid-name

    # MQTT Publication Topic(s)
    pub_source = os.getenv("PUB_SOURCE", None)
    if pub_source is None:
        # get the hostname from the environment
        pub_source = subprocess.getoutput("hostname").replace(".local", "")

    pub_topic_root = f"KTBMES/{pub_source}/smartplugs"
    pub_topic_shelly = f"{pub_topic_root}/shelly"  # pylint: disable=unused-variable

    # MQTT Subscription Topic(s)
    sub_topics: list = ["Shelly/#"]

    # ############################ Logger Setup ############################ #

    logger = ktb_logger(
        clear_logger=True,
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        file_handler="Data/shelly.log",
    )

    # ############################ MQTT Setup ############################ #

    broker_name = BROKER_NAME
    mqtt_manager = MQTTManager(
        broker_config=BROKER_CONFIG[broker_name],
        subscribe_topics=sub_topics,
        publish_topic_root=pub_topic_root,
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
