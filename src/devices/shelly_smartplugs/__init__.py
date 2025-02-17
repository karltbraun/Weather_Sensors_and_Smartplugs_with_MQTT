"""
Shelly Smart Plugs Package

This package provides functionality for controlling and monitoring Shelly smart plugs
via MQTT. It includes models for device state and commands, and a controller for
managing device interactions.

Typical usage:
    from src.devices.shelly_smartplugs import ShellyPlugController, ShellyPlugCommand

    controller = ShellyPlugController()
    command = ShellyPlugCommand(device_id="shellyplug-s-12345", command="on")
"""

from .controller import ShellyPlugController
from .models import ShellyPlugCommand, ShellyPlugStatus

__all__ = [
    "ShellyPlugStatus",
    "ShellyPlugCommand",
    "ShellyPlugController",
]

__version__ = "0.1.0"
