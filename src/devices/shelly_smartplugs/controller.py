"""
Shelly Smart Plug Controller.
Handles the control and monitoring of Shelly smart plugs via MQTT.
Supports various Shelly plug models including Plug S and Plus series.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from src.mqtt_framework.message_handler import BaseMessageHandler
from src.mqtt_framework.queue_manager import QueuedMessage


@dataclass
class ShellyPlugState:
    """
    Represents the current state of a Shelly smart plug.

    Attributes:
        device_id: Unique identifier for the plug
        is_on: Current power state
        power_watts: Current power consumption in watts
        energy_wh: Total energy consumption in watt-hours
        temperature: Device temperature in Celsius
        overtemperature: Whether device is overheating
        last_update: Timestamp of last state update
    """

    device_id: str
    is_on: bool = False
    power_watts: float = 0.0
    energy_wh: float = 0.0
    temperature: Optional[float] = None
    overtemperature: bool = False
    last_update: datetime = None

    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now()


class ShellyPlugController(BaseMessageHandler):
    """
    Controller for Shelly smart plugs.
    Handles state management and command processing for Shelly devices.
    """

    def __init__(self):
        """Initialize the controller with empty state storage."""
        super().__init__()
        self.plug_states: Dict[str, ShellyPlugState] = {}

    def process_message(
        self, message: QueuedMessage
    ) -> Optional[QueuedMessage]:
        """
        Process incoming Shelly plug messages.

        Args:
            message: Incoming MQTT message

        Returns:
            Optional response message if needed

        Raises:
            ValueError: If message format is invalid
        """
        try:
            # Extract device ID from topic
            device_id = self._parse_device_id(message.topic)
            if not device_id:
                return None

            if "status" in message.topic:
                return self._handle_status_update(
                    device_id, message.payload
                )
            elif "command" in message.topic:
                return self._handle_command(device_id, message.payload)

        except Exception as e:
            print(f"Error processing message: {e}")
        return None

    def _handle_status_update(
        self, device_id: str, payload: Dict[str, Any]
    ) -> Optional[QueuedMessage]:
        """
        Handle status update messages from Shelly plugs.

        Args:
            device_id: ID of the reporting device
            payload: Status data from device

        Returns:
            None as status updates don't require responses
        """
        state = self.plug_states.get(device_id)
        if not state:
            state = ShellyPlugState(device_id=device_id)
            self.plug_states[device_id] = state

        # Update state from payload
        state.is_on = payload.get("relay0", state.is_on)
        state.power_watts = payload.get("power", state.power_watts)
        state.energy_wh = payload.get("energy", state.energy_wh)
        state.temperature = payload.get("temperature", state.temperature)
        state.overtemperature = payload.get(
            "overtemperature", state.overtemperature
        )
        state.last_update = datetime.now()

        return None

    def _handle_command(
        self, device_id: str, payload: Dict[str, Any]
    ) -> Optional[QueuedMessage]:
        """
        Handle command messages for Shelly plugs.

        Args:
            device_id: Target device ID
            payload: Command data

        Returns:
            Command acknowledgment message if needed
        """
        command = payload.get("command")
        if not command:
            return None

        if command in ["on", "off"]:
            return QueuedMessage(
                topic=f"shellies/{device_id}/relay/0/command",
                payload=command,
            )
        return None

    def _parse_device_id(self, topic: str) -> Optional[str]:
        """Extract device ID from MQTT topic."""
        parts = topic.split("/")
        if len(parts) >= 2 and parts[0] == "shellies":
            return parts[1]
        return None

    def format_message(self, message: QueuedMessage) -> Dict[str, Any]:
        """Format message for publishing."""
        if isinstance(message.payload, dict):
            return message.payload
        return {"command": str(message.payload)}
