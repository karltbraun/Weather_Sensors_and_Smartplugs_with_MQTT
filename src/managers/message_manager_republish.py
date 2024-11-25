"""process_messages - routines to process incoming messages, which are individual
tags (attributes: values) from a sensor device.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Tuple

import paho.mqtt.client as mqtt

from src.utils.device_maps import my_sensors_id_map
from src.utils.misc_utils import celsius_to_fahrenheit

logging.basicConfig(level=logging.DEBUG)

# ##############################################################################
#                       Meesage Manager Class                                  #
# ##############################################################################


class MessageManager:
    """MessageManager - class to manage incoming messages from the MQTT broker"""

    def __init__(self):
        self.devices = {}

    # ##############################################################################
    #                       process_message
    # ##############################################################################

    def process_message(
        self,
        msg: mqtt.MQTTMessage,
        devices: Dict[str, Any],
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

        # ########################## transform_tag ########################## #

        tag_transform_map = {
            "id": "device_id",
            "protocol": "protocol_id",
        }

        def transform_tag(topic: str) -> str:
            """
            Transform the tag from the MQTT topic
            some original tag items don't match the tag names we use in devices
            for example: 'id' (not very descriptive) is transformed to 'device_id'
            if we don't have a transformation for the tag, we return the original tag
            """
            current_tag = topic.split("/")[-1]
            return tag_transform_map.get(current_tag, current_tag)

        # ########################## get_device_name ########################## #

        def get_device_name(device_id: str) -> str:
            """Get the device name from the my_sensors_id_map"""
            device_info = my_sensors_id_map.get(device_id, {})
            return device_info.get("sensor_name", f"UNKNOWN_{device_id}")

        # ########################## process message ########################## #

        # topic will look like this: KTBMES/Pi1/sensors/raw/200/noise
        #   where device_id = "200" and tag = "noise"
        device_id = msg.topic.split("/")[-2]
        tag = transform_tag(msg.topic)
        payload = msg.payload

        # update the device dictionary with the new data
        if device_id not in devices:
            logging.debug(
                "%s: creating new device entry for device %s\n",
                my_name,
                device_id,
            )
            current_time = datetime.now()
            devices[device_id] = {
                "device_id": device_id,
                "device_name": "NO_DEV_NAME",
                "protocol_id": "-1",
                "protocol_name": "NO_PROTOCOL_NAME",
                "protocol_description": "NO_PROTOCOL_DESCRIPTION",
                "temperature_C": -999.0,
                "temperature_F": -999.0,
                "humidity": -999.0,
                "battery_ok": -1,
                "channel": "-1",
                "rssi": -999.0,
                "snr": -999.0,
                "noise": -999.0,
                "time_last_seen_ts": current_time.timestamp(),
                "time_last_seen_iso": current_time.isoformat(),
                "time_last_published_ts": 0,
                "time_last_published_iso": "NEVER",
            }

        payload = self.normalize_payload(tag, payload)

        # update the device entry
        logging.debug(
            "%s: updating device %s\n\ttag: %s\n\tpayload: %s  type: %s\n",
            my_name,
            device_id,
            tag,
            payload,
            type(payload),
        )
        devices[device_id][tag] = payload
        ts = datetime.now()
        devices[device_id]["time_last_seen_ts"] = ts.timestamp()
        devices[device_id]["time_last_seen_iso"] = ts.isoformat()

        # if this is a protocol tag (a protocol ID), add the protocol name
        #   and description to the device dictionary
        if tag == "protocol_id":
            devices[device_id]["protocol_id"] = (
                payload  # Update protocol_id
            )
            (
                devices[device_id]["protocol_name"],
                devices[device_id]["protocol_description"],
            ) = self.get_proto_info(payload, protocol_manager)
            logging.debug(
                "%s: Protocol Tag - adding protocol information\n"
                "\tdevice_id: %s\n\tprotocol: %s\n\tprotocol_name: %s\n",
                my_name,
                device_id,
                payload,
                devices[device_id]["protocol_name"],
            )

        # if the tag is "temperature_C", add in the temperature in Fahrenheit
        elif tag == "temperature_C":
            temperature_f = celsius_to_fahrenheit(payload)
            logging.debug(
                "%s: tag is temperature_C - adding temperature_F\n"
                "\tdevice_id: %s\n"
                "\ttemperature_C: %s\n\ttemperature_F: %s",
                my_name,
                device_id,
                payload,
                temperature_f,
            )
            devices[device_id]["temperature_F"] = temperature_f

        # update the timestamp for the time we last saw data from this device
        devices[device_id]["last_update_ts"] = datetime.now().isoformat()
        devices[device_id]["device_name"] = get_device_name(device_id)

        logging.debug(
            "%s: updated device with ID %s:\n\tdevice_name: %s\n\ttag: %s\n\tprotocol_id: %s\n",
            my_name,
            device_id,
            devices[device_id]["device_name"],
            tag,
            devices[device_id]["protocol_id"],
        )

    # ############################ normalize_payload ############################ #

    def normalize_payload(self, tag, current_payload: bytes) -> Any:
        """
        Normalize the payload based on the provided tag.

        Args:
            tag (str): The tag indicating the type of the payload.
            current_payload (bytes): The payload data in bytes.

        Returns:
            Any: The normalized payload. The type of the returned value depends on the tag:
                - "time": Decoded as a UTF-8 string.
                - "protocol", "channel", "battery_ok":
                    Decoded as an integer if possible, otherwise as a string.
                - "temperature_C", "humidity", "freq", "rssi", "snr", "noise": Decoded as a float.
                - "id", "mic", "mod": Decoded as a UTF-8 string.
                - Any other tag: Attempted to be decoded as a string,
                    otherwise "*** BAD PAYLOAD ***".

        Logs:
            Logs an error message if an exception occurs during decoding.
        """
        my_name = "normalize_payload"

        new_payload = "*** UNKNOWN PAYLOAD ***"

        try:
            match tag:
                case "time":
                    # time payloads are strings
                    new_payload = current_payload.decode("utf-8")

                case "protocol":
                    new_payload = str(int(current_payload.decode("utf-8")))
                    logging.debug(
                        "\n------------------------------------------------------------------\n"
                        "%s: protocol payload\n\tcurrent_payload: %s\n\tnew_payload: %s\n"
                        "------------------------------------------------------------------\n",
                        my_name,
                        current_payload,
                        new_payload,
                    )

                case "channel" | "battery_ok":
                    # these payloads may be a single byte integer or character
                    try:
                        new_payload = int.from_bytes(
                            current_payload, byteorder="big"
                        )
                    except ValueError:
                        # note: subsequent exceptions are caught by the
                        # outer try-except block
                        new_payload = current_payload.decode("utf-8")

                case (
                    "temperature_C"
                    | "humidity"
                    | "freq"
                    | "rssi"
                    | "snr"
                    | "noise"
                ):
                    # these payloads are floats
                    new_payload = float(current_payload.decode("utf-8"))

                case "id" | "mic" | "mod":
                    # these payloads are strings
                    new_payload = current_payload.decode("utf-8")

                case _:
                    new_payload = current_payload.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as e:
            logging.error("Error decoding payload: %s", e)
            new_payload = "*** BAD PAYLOAD ***"

        return new_payload

    # ############################ get_proto_info ############################ #

    def get_proto_info(
        self, payload: bytes, protocol_manager
    ) -> Tuple[str, str]:
        """assuming the payload is protocol ID, get the protocol name and description"""
        my_name = "get_proto_info"

        def normalize_protocol(protocol_id: Any) -> str:
            """ensure protocol is encapsulated as a string"""
            new_protocol_id = None

            if isinstance(protocol_id, int):
                # if protocol_id is an integer, convert it to a string
                new_protocol_id = str(protocol_id)
            elif isinstance(protocol_id, bytes):
                # if protocol_id is bytes, decode it to a string
                new_protocol_id = payload.decode("utf-8")
            elif isinstance(protocol_id, str):
                new_protocol_id = protocol_id
            else:
                raise ValueError(
                    f"{my_name}: get_proto_info: payload is not a string: {payload}"
                )

            logging.debug(
                "\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
                "normalize_protocol:\n"
                "\tprotocol_id: %s\n  type(protocol_id): %s\n"
                "\tnew_protocol_id: %s\n  type(new_protocol_id): %s\n"
                "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n",
                protocol_id,
                type(protocol_id),
                new_protocol_id,
                type(new_protocol_id),
            )
            return protocol_id

        p_id = normalize_protocol(payload)
        p_info: Dict[str, str] = protocol_manager.get_protocol_info(p_id)

        if p_info is None or p_info == {}:
            p_name = "**ERROR**"
            p_description = "Protocol not in protocol definitions"
            logging.debug(
                "%s: Error parsing message: \n\t%s\n", my_name, p_id
            )
        else:
            try:
                p_name = p_info["name"]
                p_description = p_info["protocol_description"]
            except KeyError as ex:
                raise ValueError(
                    f"{my_name}: Error parsing protocol info: {ex}\n"
                    f"\t{p_info}\n"
                ) from ex

        logging.debug(
            "%s:\n\tProtocol ID: %s\n\t: %s\n", my_name, p_id, p_name
        )

        return p_name, p_description
