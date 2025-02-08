"""message_manager_republish.py

This module contains the MessageManager class, which is responsible for processing incoming
messages from an MQTT broker. The messages are individual tags (attributes: values) from
sensor devices. The class maintains a dictionary of devices and their data, updating it with
each incoming message. It also includes routines to normalize payloads and retrieve protocol
information.

Classes:
    MessageManager: Manages incoming messages from the MQTT broker.

Functions:
    process_message(msg, devices, protocol_manager): Processes a single message from the message queue.
    normalize_payload(tag, current_payload): Normalizes the payload based on the provided tag.
    get_proto_info(payload, protocol_manager): Retrieves protocol name and description based on the protocol ID.
"""

import logging
from typing import Any, Tuple

import paho.mqtt.client as mqtt

from src.managers.device_manager import Device, DeviceRegistry
from src.managers.local_sensor_manager import LocalSensorManager

# ##############################################################################
#                       Meesage Manager Class                                  #
# ##############################################################################


class MessageManager:
    """MessageManager - class to manage incoming messages from the MQTT broker"""

    def __init__(self, local_sensor_manager: LocalSensorManager):
        self.local_sensor_manager = local_sensor_manager
        self.device_registry = DeviceRegistry()

    def device_name_from_id_set(
        self, device_id: str, device_name: str
    ) -> None:
        """Set the device name from the device ID"""
        device = self.device_registry.get_device(device_id)
        device.device["device_name"] = device_name

    # ##############################################################################
    #                       process_message
    # ##############################################################################

    def process_message(
        self,
        msg: mqtt.MQTTMessage,
        protocol_manager,
    ) -> None:
        """process_message - process a single message from the message queue
        The message is on a subscribed-to topic received from the MQTT broker
        * Determine the device from the topic string
        * we keep a dictionary of devices and their data
        * * The dictionary is indexed by the device ID
        * * if we don't have an entry for the device in the received message,
            we create a new entry
        * * Update the entry for the device with the current data
            note that the data is 1 attribute of the device (eg: temperature, noise, id#, etc)
        * * some other routine will periodically publish the data in the dictionary under
            new topics
        """
        my_name = "process_message"

        #
        # Get the device ID and a normalized tag from the topic

        device_id, tag = self.parse_topic(msg.topic)
        logging.debug(
            "%s:\n"
            "\tProcessing message with device id %s and tag %s => %s\n",
            my_name,
            device_id,
            tag,
            Device.normalize_tag_name(tag),
        )
        tag = Device.normalize_tag_name(tag)

        #
        # get a normalized payload (accounts for different data types)
        #

        try:
            payload = self.normalize_payload(tag, msg.payload)
            # get the device name. If we do not yet have that device recorded, set up the device
            # with a placeholder name
            device: Device = self.device_registry.get_device(device_id)
            if device.device_name() is None:
                raise ValueError(
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                    f"{my_name}: Device name not set for device ID {device_id}\n"
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                )

            #
            # set device attribute values
            #

            device.device_name_from_id_set(device_id)
            device.tag_value_set(tag, payload)
            device.last_last_seen_now_set()

        except Exception as e:
            logging.error(
                "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                "%s: Failed to process message: %s\n"
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
                my_name,
                e,
            )
            raise e

        #
        # see if any transformations or added information is needed
        #

        if tag == "protocol_id":
            # if this is a protocol tag (a protocol ID), add the protocol name
            #   and description to the device dictionary

            protocol_id = payload
            protocol_name, protocol_description = (
                protocol_manager.protocol_info(protocol_id)
            )
            if protocol_name is None or protocol_description is None:
                raise ValueError(
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                    f"{my_name}: Protocol ID \\{protocol_id}\\ not found\n"
                    f"\ttag: {tag}\n\tpayload: {payload}\n"
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                )

            device.protocol_id_set(protocol_id)
            device.protocol_name_set(protocol_name)
            device.protocol_description_set(protocol_description)

            # well, this seems redundant
            # device.protocol_name_set(protocol_name)
            # device.protocol_description_set(protocol_description)

            logging.debug(
                "%s: Protocol Tag - adding protocol information\n"
                "\tdevice_id: %s\n\tprotocol: %s\n\tprotocol_name: %s\n",
                my_name,
                device_id,
                payload,
                protocol_name,
            )

        elif tag == "temperature_C":
            # if the tag is "temperature_C", add in the temperature in Fahrenheit
            # NOTE: if the device natively has a temperature_F, it will also have a
            #   temperature_C, at least as far as I have seen.  So we just do our own conversion
            device.temperature_F_set_from_C(payload)
            logging.debug(
                "%s: updated device with ID %s:\n\tdevice_name: %s\n\ttag: %s\n\tprotocol_id: %s\n",
                my_name,
                device_id,
                device.device_name(),
                device.tag_value(tag),
                device.protocol_id(),
            )

        # TODO: Correct the tag value

        elif tag == "pressure_kPa":
            # convert tire pressure in kPa to psi
            device.kpa_set(payload)
            device.psi_from_kpa_set(payload)

        # no additional processing needed

    # ###################################################################### #
    #                             parse_topic
    # ###################################################################### #

    def parse_topic(self, topic: str) -> Tuple[str, str]:
        """parse_topic - parse the topic string to extract the device ID and attribute"""
        parts = topic.split("/")
        if len(parts) < 3:
            raise ValueError("parse_topics: Invalid topic format")

        device_id = parts[-2]
        attribute = parts[-1]
        return device_id, attribute

    # ###################################################################### #
    #                             normalize_payload
    # ###################################################################### #

    def normalize_payload(self, tag: str, current_payload: bytes) -> Any:
        """normalize_payload - normalize the payload based on the tag.
        different payloads are formatted differently depending on the tag"""

        try:
            match tag:
                # many of these could be combined, but I'm keeping them separate
                # separate as I've found some rare devices that don't follow the
                #   expected format

                case "time":
                    # time is just a string representation of the time
                    return current_payload.decode("utf-8")

                case "protocol":
                    # protocol should be a string.  Usually looks like
                    # a string representation of a int, but sometimes
                    # has hex characters like a MAC Address in it
                    return str(int(current_payload.decode("utf-8")))

                case "channel":
                    # channel is an integer
                    # turns out some devices have non-numeric values for channel
                    return current_payload.decode("utf-8")

                case "battery_ok":
                    # battery_OK is usually an integer, but sometimes a string
                    return current_payload.decode("utf-8")

                case (
                    "temperature_C"
                    | "humidity"
                    | "freq"
                    | "rssi"
                    | "snr"
                    | "noise"
                ):
                    # these are all floats
                    return float(current_payload.decode("utf-8"))

                case "id" | "mic" | "mod":
                    # these are all strings
                    return current_payload.decode("utf-8")

                case _:
                    return current_payload.decode(
                        "utf-8", errors="replace"
                    )

        except Exception as e:
            logging.error("Failed to normalize payload: %s", e)
            raise e
