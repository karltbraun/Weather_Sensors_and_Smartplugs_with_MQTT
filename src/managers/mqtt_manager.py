"""temp module docstring"""

import json
import logging
from datetime import datetime
from queue import Queue

import paho.mqtt.client as mqtt

# from typing import Any, Dict, List
# from typing import List


# ###################################################################### #
#                             MQTTManager
# ###################################################################### #


class MQTTManager:
    """tmp docstring - update after code changes"""

    def __init__(
        self,
        broker_config,
        subscribe_topics="#",
        publish_topic_root="DEFAULT_TOPIC",
    ):
        self.broker_config = broker_config
        self.subscribe_topics: list = subscribe_topics
        self.publish_topic_root: str = publish_topic_root
        self.message_queue_in = Queue()
        self.message_queue_out = Queue()
        self.client = self.mqtt_setup()

    # ############################ mqtt_setup ############################ #

    def mqtt_setup(self) -> mqtt.Client:
        """
        Sets up and returns an MQTT client with the specified configuration.
        Returns:
            mqtt.Client: Configured MQTT client instance.
        """

        client = mqtt.Client()
        # userdata = {
        #     "message_queue": self.message_queue_in,
        #     "subscribed_topics": self.subscribe_topics,
        #     "publish_topic_root": self.publish_topic_root,
        # }
        # client.user_data_set(userdata)

        # set the callback functions
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_log = self.on_log
        client.on_disconnect = self.on_disconnect

        # set the username and password
        client.username_pw_set(
            self.broker_config["MQTT_USERNAME"],
            self.broker_config["MQTT_PASSWORD"],
        )

        # connect to the broker
        client.connect(
            self.broker_config["MQTT_BROKER_ADDRESS"],
            self.broker_config["MQTT_BROKER_PORT"],
            self.broker_config["MQTT_KEEPALIVE"],
        )

        return client

    # ############################ ON_CONNECT  ############################ #

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """
        On Connect Callback function for MQTT client.
        """

        # topics = userdata["subscribed_topics"]
        topics: list = self.subscribe_topics

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            tborder = "*" * 60
            bborder = tborder

            lmsg = (
                f"\n{tborder}\n"
                "On_Connect:\n"
                f"\tFlags: {flags}\n"
                f"\tResult Code: {rc}\n"
                f"\tProperties: {properties}\n"
                f"{bborder}"
            )
            logging.debug(lmsg)

        for topic in topics:
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                emsg = f"Subscribing to topic: {topic}"
                logging.debug(emsg)
                client.subscribe(topic)

    # ############################ ON_MESSAGE ############################ #

    def on_message(
        self,
        client,
        userdata,
        msg: mqtt.MQTTMessage,  # pylint: disable=unused-argument
    ) -> None:
        """
        Callback function for when a message is received from the MQTT broker.
        It puts the received message into the inbound message queue for further processing.

        Args:
            client (paho.mqtt.client.Client): The MQTT client instance.
            userdata (any): not used
            msg (paho.mqtt.client.MQTTMessage): The received MQTT message.

        Returns:
            None
        """

        self.message_queue_in.put(msg)

    # ############################ ON_LOG  ############################ #

    def on_log(
        self,
        client,
        userdata,
        level,
        buf,  # pylint: disable=unused-argument
    ) -> None:
        """
        Callback function for MQTT client logging.

        This function is called when the MQTT client has log information. It filters out
        specific log messages that are not needed and logs the rest.

        Args:
            client (paho.mqtt.client.Client): The MQTT client instance.
            userdata (any): User-defined data of any type that is passed to the callback.
            level (int): The severity level of the log message.
            buf (str): The log message.

        Returns:
            None
        """

        exclude_messages = [
            "Received PUBLISH",
            "Sending PINGREQ",
            "Received PINGRESP",
        ]

        buf_parts = buf.split(" ")
        buf_prelude = f"{buf_parts[0]} {buf_parts[1]}"
        if buf_prelude not in exclude_messages:
            msg = (
                f"Log Entry:\n"
                f"\tlevel: {int(level)}\n"
                f"\tmessage: {buf}\n"
            )
            logging.info(msg)

    # ############################ ON_DISCONNECT ############################ #

    def on_disconnect(  # pylint: disable=too-many-arguments
        self,
        client,  # pylint: disable=unused-argument
        userdata,
        disconnect_flags,
        rc=None,
        properties=None,
    ) -> None:
        """
        Description

        Args:
            param1 (type): Description
            param2 (type): Description

        Returns:
            type: Description
        """
        if rc == 0 or rc is None:
            emsg = (
                f"Graceful disconnection at {datetime.now().isoformat()}"
            )
            logging.debug(emsg)
        else:
            emsg = (
                f"Unexpected disconnection at {datetime.now().isoformat()}\n"
                f"\tDisconnect_flags: {disconnect_flags}\n"
                f"\tReason Code: {rc}\n"
                f"\t(type of Reason Code is: {type(rc)}\n"
                f"\tProperties: {properties}"
                # f"\tUserdata: {userdata}"
            )
            logging.debug(emsg)

    # ############################ PUBLISH_FLAT  ############################ #

    def publish_flat(
        self,
        topic: str,
        payload: str,
        qos=0,  # pylint: disable=unused-argument
        retain=False,  # pylint: disable=unused-argument
        properties=None,  # pylint: disable=unused-argument
    ) -> None:
        """
        Publish a message to a specified MQTT topic.

        Args:
            client (mqtt.Client): The MQTT client instance used to publish the message.
            topic (str): The topic to which the message will be published.
            value (Any): The message payload to be published.

        Returns:
            None
        """

        my_name = "publish_flat"
        current_time = datetime.now().isoformat()
        # publish the payload to the topic
        emsg = (
            f"\n"
            f"---------------{my_name}: Publishing Message {current_time} ---------------\n"
            f"Topic {topic}:\n\t{payload}\n"
            f"------------------------------------------------------------------------------"
        )
        logging.debug(emsg)
        self.client.publish(topic, payload)

    # ############################ PUBLISH_DICT ############################ #

    def publish_dict(
        self,
        topic: str,
        device_info: dict,
        qos=0,  # pylint: disable=unused-argument
        retain=False,  # pylint: disable=unused-argument
        properties=None,  # pylint: disable=unused-argument
    ) -> None:
        """
        Create the topic
            Topic should be the BASE_TOPIC + DeviceName
        Ensure the message is formatted correctly
            Should include all of the fields stored in he devices entry (device_info)
        publish
        """
        my_name = "publish_dict"

        current_time = datetime.now().isoformat()
        try:
            json_message = json.dumps(device_info)
            emsg = (
                f"\n"
                f"---------------{my_name}: Publishing Message {current_time} ---------------\n"
                f"Topic {topic}:\n\t{json_message}\n"
                f"------------------------------------------------------------------------------"
            )
            logging.debug(emsg)
        except (TypeError, ValueError) as e:
            emsg = (
                f"{my_name}:\n"
                f"Error decoding json: {e}\n"
                f"device_info: {device_info}"
            )
            logging.error(emsg)

        #! TODO: Add QoS and Retain options
        self.client.publish(topic, json_message)


#
