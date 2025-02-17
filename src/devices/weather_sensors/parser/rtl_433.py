"""
RTL433 message parser.
Handles parsing of JSON messages from RTL433 software-defined radio output
into WeatherReading objects.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from ..models import WeatherReading


class RTL433Parser:
    """
    Parser for RTL433 JSON messages.

    Converts JSON data from RTL433 into WeatherReading objects,
    handling different sensor models and their specific data formats.
    """

    def parse(
        self, payload: str | Dict[str, Any]
    ) -> Optional[WeatherReading]:
        """
        Parse RTL433 JSON message into WeatherReading.

        Args:
            payload: JSON string or dictionary containing sensor data

        Returns:
            WeatherReading object if parsing successful, None otherwise

        Raises:
            json.JSONDecodeError: If payload is string and invalid JSON
        """
        try:
            # Convert string payload to dict if needed
            data = (
                json.loads(payload)
                if isinstance(payload, str)
                else payload
            )

            # Extract common fields
            reading = WeatherReading(
                temperature=self._get_temperature(data),
                humidity=data.get("humidity"),
                battery=self._get_battery_status(data),
                sensor_id=str(data.get("id", "")),
                model=data.get("model", "unknown"),
                timestamp=self._get_timestamp(data),
            )

            return reading

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing RTL433 message: {e}")
            return None

    def _get_temperature(self, data: Dict[str, Any]) -> float:
        """
        Extract temperature from data, converting if needed.

        Args:
            data: Dictionary containing sensor data

        Returns:
            Temperature in Celsius

        Raises:
            ValueError: If temperature cannot be extracted
        """
        # Try different possible temperature field names
        if "temperature_C" in data:
            return float(data["temperature_C"])
        elif "temperature" in data:
            return float(data["temperature"])
        raise ValueError("No temperature field found in data")

    def _get_battery_status(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Extract battery status from data.

        Args:
            data: Dictionary containing sensor data

        Returns:
            1 if battery OK, 0 if battery low, None if unknown
        """
        if "battery_ok" in data:
            return 1 if data["battery_ok"] else 0
        elif "battery" in data:
            return 1 if data["battery"] else 0
        return None

    def _get_timestamp(self, data: Dict[str, Any]) -> datetime:
        """
        Extract timestamp from data or use current time.

        Args:
            data: Dictionary containing sensor data

        Returns:
            datetime object representing the reading time
        """
        if "time" in data:
            try:
                return datetime.fromtimestamp(float(data["time"]))
            except (ValueError, TypeError):
                pass
        return datetime.now()
        return datetime.now()
