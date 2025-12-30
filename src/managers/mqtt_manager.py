"""mqtt_manager.py - MQTT client management and message handling.

This module provides the MQTTManager class which handles MQTT client connections,
subscriptions, message queueing, and publishing. It includes robust connection
handling with DNS resolution, automatic reconnection, and comprehensive logging.

Key Features:
    - Automatic DNS resolution with fallback to IP addresses
    - Retry logic for initial connection with configurable attempts
    - Automatic reconnection on disconnect
    - Message queueing for both incoming and outgoing messages
    - Support for both flat (single value) and JSON (dictionary) publishing
    - Comprehensive logging of connection events and errors

Author: ktb
Updated: 2024-12-30
"""

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
        """Initialize the MQTT Manager.

        Args:
            broker_config: Dictionary containing MQTT broker configuration
                          (address, port, username, password, keepalive).
            subscribe_topics: List of topics to subscribe to, or "#" for all.
            publish_topic_root: Root topic for publishing messages.
            max_initial_retries: Maximum connection attempts at startup (default: 3).
            retry_delay: Seconds between initial connection retries (default: 5).
            max_reconnect_retries: Maximum reconnection attempts (default: 3).
            reconnect_delay: Seconds between reconnection attempts (default: 5).

        The manager creates two message queues:
            - message_queue_in: For incoming messages from subscribed topics
            - message_queue_out: For outgoing messages to be published
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
        """Configure and connect the MQTT client with retry logic.

        Performs DNS resolution, validates broker accessibility, and establishes
        the MQTT connection. Includes automatic retry with exponential backoff.
        Sets up all callback functions (on_connect, on_message, on_log, on_disconnect).

        Returns:
            Configured and connected MQTT client instance.

        Raises:
            SystemExit: If connection fails after max_initial_retries attempts.

        Note:
            Supports both hostnames (with DNS resolution) and IP addresses.
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
        """Callback executed when client successfully connects to broker.

        Subscribes to all configured topics and logs connection success.

        Args:
            client: MQTT client instance.
            userdata: User data passed to callbacks (unused).
            flags: Connection flags from broker.
            rc: Connection result code (0 = success).
            properties: MQTT v5 properties (optional).
        """

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
        """Callback for incoming MQTT messages.

        Receives messages from subscribed topics and queues them for processing.

        Args:
            client: MQTT client instance.
            userdata: User data passed to callbacks (unused).
            msg: MQTT message containing topic, payload, qos, and retain flag.

        Note:
            Messages are placed in message_queue_in for asynchronous processing.
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
        """Callback for MQTT client log messages.

        Filters out routine messages (PUBLISH, PINGREQ, PINGRESP) and logs
        significant events for debugging.

        Args:
            client: MQTT client instance.
            userdata: User data passed to callbacks (unused).
            level: Log level (integer).
            buf: Log message string.
        """

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
        """Callback for broker disconnection events with automatic reconnection.

        Handles both graceful disconnects (rc=0) and unexpected disconnections.
        Attempts to reconnect with exponential backoff up to max_reconnect_retries.

        Args:
            client: MQTT client instance.
            userdata: User data passed to callbacks (unused).
            disconnect_flags: Disconnection flags from broker.
            rc: Disconnect reason code (0 = graceful, non-zero = error).
            properties: MQTT v5 properties (optional).

        Raises:
            SystemExit: If reconnection fails after maximum attempts.
        """
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
        """Publish a single value to an MQTT topic (flat message format).

        Publishes a simple string payload to the specified topic, typically used
        for individual sensor attributes (e.g., temperature, humidity).

        Args:
            topic: Full MQTT topic path (e.g., 'KTBMES/sensors/device123/temp').
            payload: String value to publish.
            qos: Quality of Service level (default: 0, currently unused).
            retain: Whether to retain message on broker (default: False, unused).
            properties: MQTT v5 properties (optional, unused).

        Example:
            >>> manager.publish_flat('KTBMES/sensors/123/temperature', '23.5')
        """

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
        """Publish device data as JSON-formatted MQTT message.

        Converts a Device object to JSON and publishes it to the specified topic.
        Used for publishing complete device state including all attributes.

        Args:
            topic: Full MQTT topic path for device data.
            device_info: Device object containing sensor/device information.
            qos: Quality of Service level (default: 0, currently unused).
            retain: Whether to retain message on broker (default: False, unused).
            properties: MQTT v5 properties (optional, unused).

        Example:
            >>> device = Device('sensor123')
            >>> manager.publish_dict('KTBMES/devices/sensor123', device)
        """
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
