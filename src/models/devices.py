""" devices
        - class definition for devices
        - transformation maps for device ID to human-friendly names
"""

from dataclasses import dataclass

#
# Subclasses - these are used to standardize common parts of various data objects
#


@dataclass
class DeviceRadioInfo:
    """Common radio attributes - part of every device we are dealing with"""

    mic: str
    mod: str
    freq: float | None
    rssi: float | None
    snr: float | None
    noise: float | None
    channel: int | None


@dataclass
class DeviceCommon:
    """other common attributes - part of every device we are dealing with"""

    time: str
    device_name: str
    protocol_id: str
    protocol_name: str
    protocol_description: str
    device_id: str
    battery_ok: int | None


@dataclass
class TemperatureInfo:
    """Temperature information"""

    temperature_c: float | None
    temperature_f: float | None


@dataclass
class DeviceWind:
    """Wind information"""

    wind_speed: float | None
    wind_direction_deg: int | None
    wind_avg_m_s: int | None
    wind_max_m_s: int | None


@dataclass
class DeviceWeather:
    """Basic weather information"""

    humidity: float | None
    pressure_kpa: float | None
    moisture: int | None
    rain_mm: float | None


@dataclass
class DeviceUnknown:
    """for devices we don't really know yet how to parse"""

    radio: DeviceRadioInfo
    common: DeviceCommon
    device_other: dict


@dataclass
class UnknownInfo:
    """for attributes we aren't sure of"""

    unknown: str | None
    unknown_2: str | None
    unknown_3: str | None


@dataclass
class MiscInfo:
    """Misc info we aren't sure how to process"""

    flags: str | None
    moving: int | None
    learn: int | None
    code: str | None
    state: int | None
    encrypted: str | None
    wheel: int | None


@dataclass
class RadioSecondaryInfo:
    """some devices have alternate or secondary radio information"""

    freq1: float | None
    freq2: float | None


@dataclass
class DeviceTPM:
    """simple tire pressure monitor devices"""

    common: DeviceCommon
    radio: DeviceRadioInfo
    pressure_kpa: float | None
    temperature_info: TemperatureInfo | None
    repeat: int | None
    maybe_battery: int | None


@dataclass
class Device:
    """Device class - a container for all device types"""

    device_id: str
    dev_info_common: DeviceCommon
    dev_info_radio: DeviceRadioInfo
    dev_info_specific: DeviceWeather | DeviceUnknown | DeviceTPM


class DeviceRegistry:
    """A registry to hold devices with their device_id as the key"""

    def __init__(self):
        self.devices = {}

    def add_device(self, device_id: str, device: Device):
        """add a device to the registry"""
        self.devices[device_id] = device

    def get_device(self, device_id: str) -> Device | None:
        """get a device from the registry"""
        return self.devices.get(device_id)

    def remove_device(self, device_id: str):
        """remove a device from the registry"""
        if device_id in self.devices:
            del self.devices[device_id]
