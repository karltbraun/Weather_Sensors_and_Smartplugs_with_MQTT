import logging
from dataclasses import dataclass
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from .exceptions import MQTTConnectionError
from .queue_manager import MessageQueue


@dataclass
class MQTTConfig:
    """Configuration for MQTT client"""

    broker_address: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    keepalive: int = 60
    client_id: Optional[str] = None


class BaseMQTTClient:
    """Base MQTT client implementation"""

    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = mqtt.Client(
            client_id=config.client_id,
            protocol=mqtt.MQTTv311,  # Explicitly set protocol version
        )
        self.message_queue = MessageQueue()

        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        if self.config.username and self.config.password:
            self.client.username_pw_set(
                self.config.username, self.config.password
            )

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(
                self.config.broker_address,
                self.config.port,
                self.config.keepalive,
            )
            self.client.loop_start()
        except Exception as e:
            raise MQTTConnectionError(f"Failed to connect: {str(e)}")

    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            raise MQTTConnectionError(f"Connection failed with code {rc}")
        logger.info("Connected to broker")

    def _on_message(self, client, userdata, message):
        """Minimal processing in callback - just queue the message"""
        self.message_queue.put(message)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.reconnect()

    def reconnect(self):
        """Attempt to reconnect to the broker"""
        try:
            self.client.reconnect()
        except Exception as e:
            raise MQTTConnectionError(f"Failed to reconnect: {str(e)}")

    def subscribe(self, topics):
        """Subscribe to one or more topics"""
        if isinstance(topics, str):
            topics = [topics]
        for topic in topics:
            self.client.subscribe(topic)

    def publish(self, topic: str, payload: dict, qos: int = 0):
        """Publish a message to a topic"""
        try:
            self.client.publish(topic, payload, qos)
        except Exception as e:
            raise MQTTConnectionError(f"Failed to publish: {str(e)}")
