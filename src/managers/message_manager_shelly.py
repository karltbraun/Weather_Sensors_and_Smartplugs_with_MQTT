""" process_messages - routines to process incoming messages
        which are json payloads or single key-value pairs as put out 
        by the Shelly devices.
    tags (attributes: values) from a sensor device.
"""

import json
import logging
import os
import subprocess
from queue import Queue
from typing import Any, Dict, Tuple

import paho.mqtt.client as mqtt

from src.utils.flatten_json import flatten_json

# from src.utils.device_maps import my_sensors_id_map

logging.basicConfig(level=logging.DEBUG)

# ##############################################################################
#                       module constants
# ##############################################################################

# maps device names into rooms
DEVICE_ROOM_MAP = {"Shelly_EV": "garage", "Shelly_Lab_01": "office"}

# constant strings for creating publication topics
ENTERPRISE = "KTBMES"
DEVICE_TYPE = "smartplugs"


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

    def get_source() -> str:
        """Get the source from the hostname or environment."""
        source = os.getenv("PUB_SOURCE", None)
        if source is None:
            source = subprocess.getoutput("hostname").replace(".local", "")
        return source

    def get_room(device_name: str) -> str:
        """Get the room from the device name."""
        return DEVICE_ROOM_MAP.get(device_name, f"UNK Plug Name {device_name}")

    topic_parts = topic.split("/")

    if len(topic_parts) < 3:
        emsg = f"{my_name}: Invalid topic format"
        raise ValueError(emsg)

    source = get_source()
    device_name = topic_parts[1]
    room = get_room(device_name)  # EV, Lab, Office, etc
    tag = topic_parts[-1]

    pub_topic = f"{ENTERPRISE}/{source}/{room}/{DEVICE_TYPE}/{device_name}/{tag}"
    return pub_topic


# ##############################################################################
#                       Meesage Manager Class                                  #
# ##############################################################################


class MessageManager:
    """MessageManager - class to manage incoming messages from the MQTT broker"""

    def __init__(self):
        pass

    # ############################ process_message  ############################ #

    def process_message(self, msg: mqtt.MQTTMessage, message_queue_out: Queue) -> None:
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

        emsg = f"{my_name}:\n\tinbound topic = {topic}\n\tPayload = {payload}"
        logging.debug(emsg)

        # ######################### process json object ######################### #

        if payload.startswith("{") and payload.endswith("}"):
            # break the json object in to a list of key-value pairs for flat MQTT
            try:
                json_object = json.loads(payload)
                flattened_json: list = flatten_json(json_object)
                logging.debug(
                    "%s:\n\treturning flattened = %s", my_name, flattened_json
                )

                for item in flattened_json:
                    payload = item[2]
                    tag = item[0]
                    pub_topic2 = f"{pub_topic}/{tag}"
                    message_queue_out.put((pub_topic2, payload, qos, retain))

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
                    message_queue_out.put((pub_topic, payload, qos, retain))

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

    # ###################################################################### #
    #                             normalize_payload
    # ###################################################################### #

    def normalize_payload(self, tag, current_payload: bytes) -> Any:
        """
        Normalize the payload based on the provided tag.

        Args:
            tag (str): The tag indicating the type of the payload.
            current_payload (bytes): The payload data in bytes.

        Returns:
            Any: The normalized payload. The type of the returned value depends on the tag:
                - "time": Decoded as a UTF-8 string.
                - "protocol", "channel", "battery_ok": Decoded as an integer.
                - "temperature_C", "humidity", "freq", "rssi", "snr", "noise": Decoded as a float.
                - "id", "mic", "mod": Decoded as a UTF-8 string.
                - Any other tag: Attempted to be decoded as a string,
                    otherwise "*** BAD PAYLOAD ***".

        Logs:
            Logs an info message if the tag is unknown.
            Logs an error message if an exception occurs during decoding.
        """

        new_payload = "*** UNKNOWN PAYLOAD ***"

        match tag:
            case "time":
                # time payloads are strings
                new_payload = current_payload.decode("utf-8")

            case "protocol" | "channel" | "battery_ok":
                # these payloads may be a single byte integer or character
                new_payload_str = current_payload.decode("utf-8")
                try:
                    new_payload = int(new_payload_str)
                except ValueError:
                    new_payload = new_payload_str

            case "temperature_C" | "humidity" | "freq" | "rssi" | "snr" | "noise":
                # all of these are float conversions
                new_payload = float(current_payload.decode("utf-8"))

            case "id" | "mic" | "mod":  # string
                # all of these are string conversions
                new_payload = current_payload.decode("utf-8")

            case _:
                # doesn't match anything
                try:
                    new_payload = str(current_payload)
                    logging.info(
                        "\n"
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                        "process_message: unknown tag %s with payload %s\n"
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n",
                        tag,
                        new_payload,
                    )
                except (UnicodeDecodeError, ValueError, TypeError) as e:
                    logging.error(
                        "\n"
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                        "An error occurred: %s - %s\n"
                        "In Process Message while trying to decode payload"
                        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n",
                        type(e).__name__,
                        e,
                    )
                    print(f"An error occurred: {type(e).__name__} - {e}")
                    new_payload = "*** BAD PAYLOAD ***"

        return new_payload

    # ############################ get_proto_info ############################ #

    def get_proto_info(self, payload: bytes, protocol_manager) -> Tuple[str, str]:
        """assuming the payload is protocol ID, get the protocol name and description"""
        my_name = "get_proto_info"
        p_id = None
        if isinstance(payload, int):
            # if payload is an integer, convert it to a string
            p_id = str(payload)
        elif isinstance(payload, bytes):
            # if payload is bytes, decode it to a string
            p_id = payload.decode("utf-8")
        elif not isinstance(payload, str):
            raise ValueError(
                f"{my_name}: get_proto_info: payload is not a string: {payload}"
            )

        p_info: Dict[str, str] = protocol_manager.get_protocol_info(p_id)

        if p_info is None:
            p_name = "**ERROR**"
            p_description = "Protocol not in protocol definitions"
            lmsg = f"Error parsing message: \n\t{payload.decode('utf-8')}\n"
            logging.error(lmsg)
        else:
            p_name = p_info["name"]
            p_description = p_info["protocol_description"]

        return p_name, p_description

    # ############################ celsius_to_fahrenheit ############################ #

    def celsius_to_fahrenheit(self, celsius: float) -> float:
        """convert celsius to fahrenheit"""
        return (celsius * 9 / 5) + 32
