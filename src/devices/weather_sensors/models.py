"""
Data models for weather sensor readings.
These models represent the structure of data received from various weather sensors
and provide methods for converting to MQTT payloads.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WeatherReading:
    """
    Weather sensor reading data model.

    Attributes:
        temperature: Temperature in Celsius
        humidity: Relative humidity percentage (0-100)
        pressure: Atmospheric pressure in hPa
        battery: Battery status (0=low, 1=ok, None=unknown)
        timestamp: Time of reading
        sensor_id: Unique identifier for the sensor
        model: Sensor model name/type
    """

    temperature: float
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    battery: Optional[int] = None
    timestamp: datetime = None
    sensor_id: str = None
    model: str = None

    def __post_init__(self) -> None:
        """Set timestamp to current time if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_mqtt_payload(self) -> Dict[str, Any]:
        """
        Convert reading to MQTT message format.

        Returns:
            Dictionary containing sensor data ready for MQTT publishing
        """
        payload = {
            "temperature": self.temperature,
            "timestamp": self.timestamp.isoformat(),
            "sensor_id": self.sensor_id,
            "model": self.model,
        }

        # Only include optional fields if they have values
        if self.humidity is not None:
            payload["humidity"] = self.humidity
        if self.pressure is not None:
            payload["pressure"] = self.pressure
        if self.battery is not None:
            payload["battery"] = self.battery

        return payload
