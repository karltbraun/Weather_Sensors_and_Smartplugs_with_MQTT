"""
This module provides functionality for managing MQTT messages from Shelly smart plugs.
It includes functions for creating publication topics and processing incoming MQTT messages.
The module also defines a `MessageManager` class that handles the processing of messages
and appends processed data to an output message queue.

Module Constants:
    TOPIC_ROOT (str): The root element in the topic string.
    DEVICE_TYPE (str): The type of device, used as the third element in the topic string.

Functions:
    create_pub_topic(topic: str) -> str:

Classes:
    MessageManager:
        A class to manage incoming messages from the MQTT broker.
        Methods:
            process_message(msg: mqtt.MQTTMessage, message_queue_out: Queue) -> None:
                Processes a single MQTT message and appends the processed data to the output message queue.
            normalize_payload(payload: dict) -> dict:
                Normalize the payload based on the topic (placeholder function).

External Dependencies:
    - paho.mqtt.client as mqtt
    - json
    - logging
    - queue.Queue
    - typing.Dict, typing.Tuple
    - src.utils.flatten_json.flatten_json
    - src.utils.misc_utils.get_pub_root, src.utils.misc_utils.get_pub_source
"""

import json
import logging
from datetime import datetime
from queue import Queue

import paho.mqtt.client as mqtt

from src.utils.flatten_json import flatten_json
from src.utils.misc_utils import get_pub_root, get_pub_source

# from typing import Dict, Tuple


# from src.utils.device_maps import my_sensors_id_map

logging.basicConfig(level=logging.DEBUG)

# ##############################################################################
#                       module constants
# ##############################################################################

# maps device names into rooms
# TODO: this should be moved to a json file the way other maps are done
DEVICE_ROOM_MAP = {"Shelly_EV": "garage", "Shelly_Lab_01": "office"}

# constant strings for creating publication topics
TOPIC_ROOT = "KTBMES"  # first element in the topic string
DEVICE_TYPE = (
    "smartplugs"  # should be the third element in the topic string
)

# Sample topic string: KTBMES/hostname/room/smartplugs/device_name/tag

# ##############################################################################
#                       create_pub_topic
# ##############################################################################


def create_pub_topic(topic: str) -> str:
    """
    Create a publication topic string based on the given topic.

    This function takes an input topic string, parses it, and constructs a new
    topic string for publication. The new topic string is constructed using
    predefined constants and mappings.

    Args:
        topic (str): The input topic string in the format "prefix/device_name/tag".

    External Values:
        DEVICE_ROOM_MAP (dict): A mapping of device names to room names.
        os.getenv("PUB_SOURCE", None): The source name from the environment.
            If not set, the source name is the hostname without the ".local" suffix.

    Returns:
        str: The constructed publication topic string.

    Raises:
        ValueError: If the input topic string does not have at least three parts.
    """
    my_name = "create_pub_topic"

    def get_room(device_name: str) -> str:
        """Get the room from the device name."""
        return DEVICE_ROOM_MAP.get(
            device_name, f"UNK Plug Name {device_name}"
        )

    topic_parts = topic.split("/")

    if len(topic_parts) < 3:
        emsg = (
            f"/n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            f"{my_name}: Invalid topic format -- too few parts: {topic}"
            f"/n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        )
        raise ValueError(emsg)

    root = get_pub_root()
    source = get_pub_source()  # get the hostname of the publishing device
    device_name = topic_parts[1]  # get the device name from the topic
    room = get_room(device_name)  # EV, Lab, Office, etc
    tag = topic_parts[-1]

    pub_topic = f"{root}/{source}/{room}/{DEVICE_TYPE}/{device_name}/{tag}"
    return pub_topic


# ##############################################################################
#                       Meesage Manager Class                                  #
# ##############################################################################


class MessageManager:
    """MessageManager - class to manage incoming messages from the MQTT broker"""

    def __init__(self):
        pass

    # ############################ process_message  ############################ #

    def process_message(
        self, msg: mqtt.MQTTMessage, message_queue_out: Queue
    ) -> None:
        """process_message -
        Processes a single MQTT message and appends the processed data to the
        output message queue.  The function handles different types of payloads
        including JSON objects, JSON arrays, strings, and numeric values. It decodes
        the payload, processes it according to its type,
        and appends the processed message to the output queue.
        Args:
            msg (mqtt.MQTTMessage): The MQTT message to process.
                It contains the topic and payload.
            message_queue_out (Queue): The queue to which the processed messages are appended.
        Raises:
            ValueError: If the payload cannot be decoded or if the JSON payload is invalid.
        Returns:
            None
            message_queue_out has new outbound messages appended to it.
        """

        my_name = "process_message"

        # Get the topic and payload from the message

        pub_topic = create_pub_topic((topic := msg.topic))
        qos = 0
        retain = False

        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(
                f"{my_name}: Failed to decode payload\n\ttopic = {topic}\n\terror = {e}"
            ) from e

        emsg = (
            f"{my_name}:\n\tinbound topic = {topic}\n\tPayload = {payload}"
        )
        logging.debug(emsg)

        # ######################### process json object ######################### #

        if payload.startswith("{") and payload.endswith("}"):
            # break the json object in to a list of key-value pairs for flat MQTT
            try:
                json_object = json.loads(payload)
                flattened_json: list = flatten_json(json_object)
                logging.debug(
                    "%s:\n\treturning flattened = %s",
                    my_name,
                    flattened_json,
                )

                for item in flattened_json:
                    payload = item[2]
                    tag = item[0]
                    pub_topic2 = f"{pub_topic}/{tag}"
                    message_queue_out.put(
                        (pub_topic2, payload, qos, retain)
                    )

                    if tag == "ts" or tag == "minute_ts":
                        new_tag = tag + "_iso"
                        time_ts: float = float(payload)
                        time_iso = datetime.fromtimestamp(
                            time_ts
                        ).isoformat()
                        message_queue_out.put(
                            (
                                f"{pub_topic}/{new_tag}",
                                time_iso,
                                qos,
                                retain,
                            )
                        )

                logging.debug(
                    "%s:\n\treturning messages to publish:\n\t%s",
                    my_name,
                    message_queue_out,
                )
                return

            except json.JSONDecodeError as e:
                raise ValueError(
                    f"{my_name}: Failed to decode JSON payload\n\ttopic = {topic}\n\terror = {e}"
                ) from e

        # ######################### process list object  ######################### #

        if payload.startswith("[") and payload.endswith("]"):
            try:
                list_object = json.loads(payload)
                if isinstance(list_object, list):
                    message_queue_out.put(
                        (pub_topic, payload, qos, retain)
                    )

                    emsg = f"{my_name}:\n\treturning list = {list_object}"
                    logging.debug(emsg)
                    return

            except json.JSONDecodeError as e:
                raise ValueError(
                    f"{my_name}:\n"
                    f"Failed to decode JSON list payload\n\ttopic = {topic}\n\terror = {e}"
                ) from e

        # ######################### process string object  ######################### #

        # if payload is a string bounded by single or double quotation marks...
        if payload.startswith(('"', "'")) and payload.endswith(('"', "'")):
            boolean_values = {
                "true": True,
                "false": False,
            }
            stripped_payload = payload.strip("\"'")

            # if stripped_payload is in the boolean_values keys,
            # make payload the appropriate boolean value
            payload = boolean_values.get(stripped_payload.lower(), None)
            if payload is None:
                # not a boolean value - assume integer or float
                payload = json.dumps(stripped_payload)

            message_queue_out.put((pub_topic, payload, qos, retain))
            return

        # ######################### process numeric object  ######################### #

        # assume the payload is a string of bytes which should just be used as the payload

        # if payload is a number, convert it to an integer or float
        # note that we do not know that payload is a string object
        #   in fact, if it was a string, we should have caught it above
        # if not isinstance(payload, (int, float)):
        #     # we don't know what the payload is
        #     payload = f"!!! Uknown Payload: {payload} !!!"
        #     logging.warning("%s:\n\t%s", my_name, payload)

        message_queue_out.put((pub_topic, payload, qos, retain))

    # # ############################ get_proto_info ############################ #

    # def get_proto_info(
    #     self, payload: bytes, protocol_manager
    # ) -> Tuple[str, str]:
    #     """assuming the payload is protocol ID, get the protocol name and description"""
    #     my_name = "get_proto_info"
    #     p_id = None
    #     if isinstance(payload, int):
    #         # if payload is an integer, convert it to a string
    #         p_id = str(payload)
    #     elif isinstance(payload, bytes):
    #         # if payload is bytes, decode it to a string
    #         p_id = payload.decode("utf-8")
    #     elif not isinstance(payload, str):
    #         raise ValueError(
    #             f"{my_name}: get_proto_info: payload is not a string: {payload}"
    #         )

    #     p_info: Dict[str, str] = protocol_manager.get_protocol_info(p_id)

    #     if p_info is None:
    #         p_name = "**ERROR**"
    #         p_description = "Protocol not in protocol definitions"
    #         lmsg = (
    #             f"Error parsing message: \n\t{payload.decode('utf-8')}\n"
    #         )
    #         logging.error(lmsg)
    #     else:
    #         p_name = p_info["name"]
    #         p_description = p_info["protocol_description"]

    #     return p_name, p_description

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
