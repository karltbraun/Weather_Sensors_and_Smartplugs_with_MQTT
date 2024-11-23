"""
Module: process_mqtt_message

This module provides functionality to process incoming MQTT messages. It includes
a function to decode the payload of an MQTT message and return a list of tuples,
each containing a tag, data type, and value. The value can be a scalar (int, float, bool),
a string, or a JSON serialized string if the payload is a list or JSON object.

Functions:
    - process_mqtt_message(msg: mqtt.MQTTMessage) -> 
        List[Tuple[str, str, Union[str, int, float, bool]]]:
        Processes an incoming MQTT message and returns a list of 
            tuples with tag, data type, and value.

Dependencies:
    - json
    - logging
    - paho.mqtt.client as mqtt
    - flatten_json.flatten_json
"""

import json
import logging
from typing import List, Tuple, Union

import paho.mqtt.client as mqtt

# from .src.utils.flatten_json import flatten_json


def process_mqtt_message(
    msg: mqtt.MQTTMessage,
) -> List[Tuple[str, str, Union[str, int, float, bool]]]:
    """
    Process an incoming MQTT message.

    This function processes an MQTT message and returns a list of tuples,
    each containing a tag (str), data type (str), and value. The value can be
    a scalar (int, float, bool), a string, or a JSON serialized string if the
    payload is a list.

    Args:
        msg (mqtt.MQTTMessage): The MQTT message to process.

    Returns:
        List[Tuple[str, str, Union[str, int, float, bool]]]: A list of tuples,
        each containing a tag (str), data type (str), and value.
    """
    my_name = "process_mqtt_message"

    # Get the topic and payload from the message
    topic = msg.topic
    topic_parts = topic.split("/")
    tag = topic_parts[-1]

    try:
        payload = msg.payload.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(
            f"{my_name}: Failed to decode payload\n\ttopic = {topic}\n\terror = {e}"
        ) from e

    emsg = f"{my_name}:\n\ttopic = {topic}\n\tPayload = {payload}"
    logging.debug(emsg)

    results: List[Tuple[str, str, Union[str, int, float, bool]]] = []

    # Check if the payload is a JSON object
    if payload.startswith("{") and payload.endswith("}"):
        try:
            json_object = json.loads(payload)
            flattened_json = flatten_json(json_object)
            emsg = f"{my_name}:\n\treturning flattened = {flattened_json}"
            logging.debug(emsg)

            for item in flattened_json:
                results.append(item)
            return results

        except json.JSONDecodeError as e:
            raise ValueError(
                f"{my_name}: Failed to decode JSON payload\n\ttopic = {topic}\n\terror = {e}"
            ) from e

    # Check if the payload is a list
    if payload.startswith("[") and payload.endswith("]"):
        try:
            list_object = json.loads(payload)
            if isinstance(list_object, list):
                json_serialized_list = json.dumps(list_object)
                results.append((tag, "list", json_serialized_list))
                emsg = f"{my_name}:\n\treturning list = {results}"
                logging.debug(emsg)
                return results
        except json.JSONDecodeError as e:
            raise ValueError(
                f"{my_name}: Failed to decode JSON list payload\n\ttopic = {topic}\n\terror = {e}"
            ) from e

    # Handle scalar values
    if payload in ["true", "True"]:
        results.append((tag, "bool", True))
    elif payload in ["false", "False"]:
        results.append((tag, "bool", False))
    elif payload.isdigit():
        results.append((tag, "int", int(payload)))
    else:
        try:
            float_payload = float(payload)
            results.append((tag, "float", float_payload))
        except ValueError:
            # Default case: return the payload as a string
            results.append((tag, "str", payload))

    emsg = f"{my_name}:\n\treturning results = {results}"
    logging.debug(emsg)

    return results
