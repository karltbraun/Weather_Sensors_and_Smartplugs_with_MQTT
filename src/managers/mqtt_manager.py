"""temp module docstring"""

import json
import logging
import socket
import time
from datetime import datetime
from queue import Queue

import paho.mqtt.client as mqtt

from src.managers.device_manager import Device

# ###################################################################### #
#                             MQTTManager
# ###################################################################### #


class MQTTManager:
    """MQTTManager is a class responsible for managing MQTT client connections, subscriptions,
    and message handling. It provides methods to set up the MQTT client, handle connection
    events, process incoming messages, log MQTT events, and publish messages to specified topics.

    Attributes:
        broker_config (dict): Configuration dictionary containing MQTT broker details such as
                              username, password, broker address, port, and keepalive interval.
        subscribe_topics (list): List of topics to subscribe to. Defaults to subscribing to all topics ("#").
        publish_topic_root (str): Root topic for publishing messages. Defaults to "DEFAULT_TOPIC".
        message_queue_in (Queue): Queue for storing incoming messages.
        message_queue_out (Queue): Queue for storing outgoing messages.
        client (mqtt.Client): Configured MQTT client instance.

    Methods:
        mqtt_setup() -> mqtt.Client:

        on_connect(client, userdata, flags, rc, properties=None):
            Callback function for when the MQTT client connects to the broker.

        on_message(client, userdata, msg: mqtt.MQTTMessage) -> None:

        on_log(client, userdata, level, buf) -> None:

        on_disconnect(client, userdata, disconnect_flags, rc=None, properties=None) -> None:
            Callback function for when the MQTT client disconnects from the broker.

        publish_flat(topic: str, payload: str, qos=0, retain=False, properties=None) -> None:
            Publishes a message to a specified MQTT topic.

        publish_dict(topic: str, device_info: Device, qos=0, retain=False, properties=None) -> None:
            Publishes a dictionary as a JSON message to a specified MQTT topic.

    """

    def __init__(
        self,
        broker_config,
        subscribe_topics="#",
        publish_topic_root="DEFAULT_TOPIC",
        max_initial_retries=3,
        retry_delay=5,
        max_reconnect_retries=3,
        reconnect_delay=5,
    ):
        """
        Initialize the MQTTManager. broker_config is a dictionary containing the
        configuration information for the MQTT broker found in broker_config.py.
        publish_topic_root is the root topic string to which subsequent subtopics will be appended.
        The message_queues are the input and output queues for the MQTTManager. The on_message callback
        function will place incoming messages in the input queue. The message processing routines may
        make use of the output queue or may publish messages directly to the broker.
        """
        self.broker_config = broker_config
        self.subscribe_topics: list = subscribe_topics
        self.publish_topic_root: str = publish_topic_root
        self.message_queue_in = Queue()
        self.message_queue_out = Queue()
        self.max_initial_retries = max_initial_retries
        self.retry_delay = retry_delay
        self.max_reconnect_retries = max_reconnect_retries
        self.reconnect_delay = reconnect_delay
        self.client = self.mqtt_setup()

    # ############################ mqtt_setup ############################ #

    def mqtt_setup(self) -> mqtt.Client:
        """
        Sets up and returns an MQTT client with the specified configuration.
        Includes DNS resolution and retry logic for initial connection.
        """
        broker_addr = self.broker_config["MQTT_BROKER_ADDRESS"]
        broker_port = self.broker_config["MQTT_BROKER_PORT"]
        broker_keepalive = self.broker_config["MQTT_KEEPALIVE"]
        broker_user = self.broker_config["MQTT_USERNAME"]
        broker_pass = self.broker_config["MQTT_PASSWORD"]

        # DNS resolution and IP validation
        def resolve_broker_address(addr):
            try:
                # Try to parse as IP
                socket.inet_aton(addr)
                return addr
            except OSError:
                # Not an IP, try DNS
                try:
                    resolved_ip = socket.gethostbyname(addr)
                    return resolved_ip
                except socket.gaierror as e:
                    logging.error(
                        f"DNS resolution failed for broker address '{addr}': {e}"
                    )
                    return None

        for attempt in range(1, self.max_initial_retries + 1):
            resolved_addr = resolve_broker_address(broker_addr)
            if not resolved_addr:
                logging.error(
                    f"Attempt {attempt}/{self.max_initial_retries}: Could not resolve broker address '{broker_addr}'. Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)
                continue
            try:
                client = mqtt.Client()
                client.on_connect = self.on_connect
                client.on_message = self.on_message
                client.on_log = self.on_log
                client.on_disconnect = self.on_disconnect
                client.username_pw_set(broker_user, broker_pass)
                client.connect(
                    resolved_addr, broker_port, broker_keepalive
                )
                logging.info(
                    f"Successfully connected to MQTT broker at {resolved_addr}:{broker_port}"
                )
                return client
            except Exception as e:
                logging.error(
                    f"Attempt {attempt}/{self.max_initial_retries}: Could not connect to MQTT broker at {resolved_addr}:{broker_port}: {e}. Retrying in {self.retry_delay}s..."
                )
                time.sleep(self.retry_delay)
        logging.critical(
            f"Failed to connect to MQTT broker '{broker_addr}' after {self.max_initial_retries} attempts. Exiting."
        )
        exit(1)

    # ############################ ON_CONNECT  ############################ #

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """executed when the client makes a successful connection to the broker"""

        # topics = userdata["subscribed_topics"]
        topics: list = self.subscribe_topics

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            tborder = "*" * 60
            bborder = tborder

            logging.debug(
                "\n%s\n"
                "On_Connect:\n"
                "\tFlags: %s\n"
                "\tResult Code: %s\n"
                "\tProperties: %s\n"
                "%s",
                tborder,
                flags,
                rc,
                properties,
                bborder,
            )

        for topic in topics:
            logging.info("Subscribing to topic: %s", topic)
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
        """Callback function for when a log message is received from the broker"""

        # messages we don't care about logging
        exclude_messages = [
            "Received PUBLISH",
            "Sending PINGREQ",
            "Sending PUBLISH",
            "Received PINGRESP",
        ]

        buf_parts = buf.split(" ")
        buf_prelude = f"{buf_parts[0]} {buf_parts[1]}"
        if buf_prelude not in exclude_messages:
            logging.info(
                "Log Entry:\n\tlevel: %d\n\tmessage: %s\n",
                int(level),
                buf,
            )

    # ############################ ON_DISCONNECT ############################ #

    def on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        rc=None,
        properties=None,
    ) -> None:
        """Callback for when a disconnect is received from the broker. Attempts to reconnect a limited number of times."""
        if rc == 0 or rc is None:
            emsg = (
                f"Graceful disconnection at {datetime.now().isoformat()}"
            )
            logging.debug(emsg)
            return
        logging.warning(
            "Unexpected disconnection at %s\n"
            "\tDisconnect_flags: %s\n"
            "\tReason Code: %s\n"
            "\t(type of Reason Code is: %s\n"
            "\tProperties: %s",
            datetime.now().isoformat(),
            disconnect_flags,
            rc,
            type(rc),
            properties,
        )
        broker_addr = self.broker_config["MQTT_BROKER_ADDRESS"]
        broker_port = self.broker_config["MQTT_BROKER_PORT"]
        broker_keepalive = self.broker_config["MQTT_KEEPALIVE"]
        broker_user = self.broker_config["MQTT_USERNAME"]
        broker_pass = self.broker_config["MQTT_PASSWORD"]

        def resolve_broker_address(addr):
            try:
                socket.inet_aton(addr)
                return addr
            except OSError:
                try:
                    resolved_ip = socket.gethostbyname(addr)
                    return resolved_ip
                except socket.gaierror as e:
                    logging.error(
                        f"DNS resolution failed for broker address '{addr}': {e}"
                    )
                    return None

        for attempt in range(1, self.max_reconnect_retries + 1):
            resolved_addr = resolve_broker_address(broker_addr)
            if not resolved_addr:
                logging.error(
                    f"Reconnect attempt {attempt}/{self.max_reconnect_retries}: Could not resolve broker address '{broker_addr}'. Retrying in {self.reconnect_delay}s..."
                )
                time.sleep(self.reconnect_delay)
                continue
            try:
                client.username_pw_set(broker_user, broker_pass)
                client.connect(
                    resolved_addr, broker_port, broker_keepalive
                )
                logging.info(
                    f"Successfully reconnected to MQTT broker at {resolved_addr}:{broker_port}"
                )
                return
            except Exception as e:
                logging.error(
                    f"Reconnect attempt {attempt}/{self.max_reconnect_retries}: Could not reconnect to MQTT broker at {resolved_addr}:{broker_port}: {e}. Retrying in {self.reconnect_delay}s..."
                )
                time.sleep(self.reconnect_delay)
        logging.critical(
            f"Failed to reconnect to MQTT broker '{broker_addr}' after {self.max_reconnect_retries} attempts. Exiting."
        )
        exit(1)

    # ############################ PUBLISH_FLAT  ############################ #

    def publish_flat(
        self,
        topic: str,
        payload: str,
        qos=0,  # pylint: disable=unused-argument
        retain=False,  # pylint: disable=unused-argument
        properties=None,  # pylint: disable=unused-argument
    ) -> None:
        """Publish a message to a flat MQTT message (key: value pair)"""

        my_name = "publish_flat"
        current_time = datetime.now().isoformat()
        # publish the payload to the topic
        logging.debug(
            "\n"
            "---------------%s: Publishing Message %s ---------------\n"
            "Topic %s:\n\t%s\n"
            "------------------------------------------------------------------------------",
            my_name,
            current_time,
            topic,
            payload,
        )
        self.client.publish(topic, payload)

    # ############################ PUBLISH_DICT ############################ #

    def publish_dict(
        self,
        topic: str,
        device_info: Device,
        qos=0,  # pylint: disable=unused-argument
        retain=False,  # pylint: disable=unused-argument
        properties=None,  # pylint: disable=unused-argument
    ) -> None:
        """publish a dictionary as a JSON message to a specified MQTT topic.
        See also publish_flat()"""

        my_name = "publish_dict"

        try:
            json_message = json.dumps(device_info)
            logging.debug(
                "\n"
                "---------------%s: Publishing Message %s ---------------\n"
                "Topic %s:\n\t%s\n"
                "------------------------------------------------------------------------------",
                my_name,
                datetime.now().isoformat(),
                topic,
                json_message,
            )
        except (TypeError, ValueError) as e:
            logging.error(
                "%s:\nError decoding json: %s\ndevice_info: %s",
                my_name,
                e,
                device_info,
            )
            raise e
            # logging.error(emsg)

        #! TODO: Add QoS and Retain options
        self.client.publish(topic, json_message)
