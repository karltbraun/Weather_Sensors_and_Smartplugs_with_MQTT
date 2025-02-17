"""
Data models for Shelly smart plug devices.
These models represent the structure of data received from and sent to Shelly devices
and provide methods for converting between MQTT payloads and Python objects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ShellyPlugStatus:
    """
    Represents a complete status update from a Shelly plug.

    Attributes:
        device_id: Unique identifier for the plug
        relay_on: Current state of the relay (True=on, False=off)
        power: Current power consumption in watts
        energy: Total energy consumption in watt-hours
        temperature: Internal temperature in Celsius
        wifi_strength: WiFi signal strength in percent
        last_update: Timestamp of the status update
    """

    device_id: str
    relay_on: bool
    power: float
    energy: float
    temperature: float
    wifi_strength: int
    last_update: datetime = None

    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.last_update is None:
            self.last_update = datetime.now()

    def to_mqtt_payload(self) -> Dict[str, Any]:
        """
        Convert status to MQTT message format.

        Returns:
            Dictionary containing formatted status data
        """
        return {
            "relay0": self.relay_on,
            "power": self.power,
            "energy": self.energy,
            "temperature": self.temperature,
            "wifi_strength": self.wifi_strength,
            "timestamp": self.last_update.isoformat(),
        }

    @classmethod
    def from_mqtt_payload(
        cls, device_id: str, payload: Dict[str, Any]
    ) -> "ShellyPlugStatus":
        """
        Create status object from MQTT payload.

        Args:
            device_id: ID of the Shelly device
            payload: Dictionary containing status data

        Returns:
            New ShellyPlugStatus instance
        """
        return cls(
            device_id=device_id,
            relay_on=payload.get("relay0", False),
            power=float(payload.get("power", 0.0)),
            energy=float(payload.get("energy", 0.0)),
            temperature=float(payload.get("temperature", 0.0)),
            wifi_strength=int(payload.get("wifi_strength", 0)),
        )


@dataclass
class ShellyPlugCommand:
    """
    Represents a command to be sent to a Shelly plug.

    Attributes:
        device_id: Target device identifier
        command: Command to execute ('on' or 'off')
        timestamp: When the command was created
    """

    device_id: str
    command: str
    timestamp: datetime = None

    def __post_init__(self):
        """Validate command and set timestamp"""
        if self.command not in ["on", "off"]:
            raise ValueError("Command must be 'on' or 'off'")
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_mqtt_payload(self) -> Dict[str, Any]:
        """
        Convert command to MQTT message format.

        Returns:
            Dictionary containing formatted command
        """
        return {
            "command": self.command,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_mqtt_payload(
        cls, device_id: str, payload: Dict[str, Any]
    ) -> "ShellyPlugCommand":
        """
        Create command object from MQTT payload.

        Args:
            device_id: ID of the target device
            payload: Dictionary containing command data

        Returns:
            New ShellyPlugCommand instance

        Raises:
            ValueError: If command is invalid
        """
        command = payload.get("command", "").lower()
        if command not in ["on", "off"]:
            raise ValueError(f"Invalid command: {command}")

        return cls(device_id=device_id, command=command)
