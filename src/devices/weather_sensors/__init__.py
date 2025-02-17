"""
Weather Sensors Package

This package provides functionality for processing and managing weather sensor data.
It includes models for weather readings, processors for handling MQTT messages,
and parsers for different sensor data formats.
"""

from .models import WeatherReading
from .parser.rtl_433 import RTL433Parser
from .processor import WeatherSensorProcessor

__all__ = [
    "WeatherReading",
    "WeatherSensorProcessor",
    "RTL433Parser",
]

__version__ = "0.1.0"
