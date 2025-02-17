"""
Weather sensor data processor.
Handles the processing of incoming weather sensor data, parsing it into
WeatherReading objects and preparing it for MQTT publication.
"""

from typing import Any, Dict, Optional

from src.mqtt_framework.message_handler import BaseMessageHandler
from src.mqtt_framework.queue_manager import QueuedMessage

from .models import WeatherReading
from .parsers.rtl433 import RTL433Parser


class WeatherSensorProcessor(BaseMessageHandler):
    """
    Processes weather sensor data from various sources.

    Attributes:
        parser: Parser instance for handling incoming data
        topic_prefix: Prefix for all published topics
    """

    def __init__(self, topic_prefix: str = "#") -> None:
        """
        Initialize the weather sensor processor.

        Args:
            topic_prefix: Prefix to use for all published topics
        """
        super().__init__()
        self.parser = RTL433Parser()
        self.topic_prefix = topic_prefix

    def process_message(
        self, message: QueuedMessage
    ) -> Optional[QueuedMessage]:
        """
        Process incoming weather sensor message.

        Args:
            message: Incoming MQTT message wrapped in QueuedMessage

        Returns:
            Processed message ready for publishing, or None if processing failed

        Raises:
            MessageProcessingError: If message processing fails
        """
        try:
            reading = self.parser.parse(message.payload)
            if reading:
                return QueuedMessage(
                    topic=f"{self.topic_prefix}/{reading.sensor_id}/data",
                    payload=reading.to_mqtt_payload(),
                )
        except Exception as e:
            # Log error but don't crash
            print(f"Error processing message: {e}")
        return None

    def format_message(self, message: QueuedMessage) -> Dict[str, Any]:
        """
        Format message for publishing.

        Args:
            message: Message to be formatted

        Returns:
            Dictionary containing formatted message data
        """
        if isinstance(message.payload, WeatherReading):
            return message.payload.to_mqtt_payload()
        return message.payload

    def get_topic_filter(self) -> str:
        """
        Get the topic filter for subscribing to weather sensor data.

        Returns:
            Topic filter string for MQTT subscription
        """
        return f"{self.topic_prefix}/+/raw"
        """
        return f"{self.topic_prefix}/+/raw"
