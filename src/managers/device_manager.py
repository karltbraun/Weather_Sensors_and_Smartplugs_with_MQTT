import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from src.managers.local_sensor_manager import LocalSensorManager

# from src.utils.misc_utils import load_json_file

# TODO: this should be read in from a json file like we do for some of the other
# TODO: maps.  Dynamically checked and read in when changed.
model_map = {
    """ device_maps.py - maps model names to standard names """
    "ACURITE-606TX": "ACURITE-606TX",
    "INFACTORY-TH": "SMARTRO-SC91",
}

#
# attribute_map -
#  maps the attribute names to something a little more readable
#

attribute_map = {
    "protocol": "protocol_id",
    "id": "device_id",
}


class Device:
    # Class variable
    local_sensor_manager: LocalSensorManager = None

    # Instance stuff
    def __init__(self, device_id: str):
        # Suffixes:
        #   _C: Celsius
        #   _F: Fahrenheit
        #   _kPa: kilopascal
        #   _psi: pounds per square inch
        #   _ts: timestamp
        #   _iso: ISO 8601 format

        # self.device_id = device_id
        current_time = datetime.now()
        self.device = {
            "device_id": device_id,
            "device_name": "NO_DEV_NAME",
            "protocol_id": "-1",
            "protocol_name": "NO_PROTOCOL_NAME",
            "protocol_description": "NO_PROTOCOL_DESCRIPTION",
            "temperature_C": -999.0,
            "temperature_F": -999.0,
            "humidity": -999.0,
            "battery_ok": -1,
            "channel": "-1",
            "rssi": -999.0,
            "snr": -999.0,
            "noise": -999.0,
            "freq": -999.0,
            "mic": "NO_MIC",
            "mod": "NO_MOD",
            "time": "NO_TIME",
            "time_last_seen_ts": current_time.timestamp(),
            "time_last_seen_iso": current_time.isoformat(),
            "time_last_published_ts": 0.0,
            "time_last_published_iso": "NEVER",
        }

    def __str__(self) -> str:
        return str(self.device)

    def tag_value(self, tag) -> Any:
        """get tag value"""
        return self.device.get(tag, None)

    def tag_value_set(self, tag: str, value: Any) -> None:
        """set tag value and update last seen time"""
        if tag not in self.device:
            logging.info(
                "\ntag_value_set: Adding tag %s with value %s to device with id %s\n",
                tag,
                value,
                self.device["device_id"],
            )
        self.device[tag] = value

    def device_name(self) -> str:
        """get device name"""
        return self.device["device_name"]

    def device_name_set(self, device_name: str) -> None:
        """set device name"""
        self.tag_value_set("device_name", device_name)

    def time_last_seen_ts(self) -> float:
        """get last seen time"""
        return self.device["time_last_seen_ts"]

    def time_last_seen_ts_set(self, timestamp: float) -> None:
        """set last seen time"""
        self.tag_value_set("time_last_seen_ts", timestamp)

    def time_last_seen_iso(self) -> str:
        """get last seen time in iso format"""
        return self.device["time_last_seen_iso"]

    def time_last_seen_iso_set(self, iso_time: str) -> None:
        """set last seen time in iso format"""
        self.tag_value_set("time_last_seen_iso", iso_time)

    def time_last_seen_now_set(self) -> float:
        """set last seen time to now in both timestamp and iso format"""
        ts = datetime.now()
        self.time_last_seen_ts_set(ts.timestamp())
        self.time_last_seen_iso_set(ts.isoformat())
        return ts.timestamp()

    def time_last_published_ts(self) -> float:
        """get last seen time"""
        return self.device["time_last_published_ts"]

    def time_last_published_ts_set(self, timestamp: float) -> None:
        """set last seen time"""
        self.tag_value_set("time_last_published_ts", timestamp)

    def time_last_published_iso(self) -> str:
        """get last seen time in iso format"""
        return self.device["time_last_published_iso"]

    def time_last_published_iso_set(self, iso_time: str) -> None:
        """set last seen time in iso format"""
        self.tag_value_set("time_last_published_iso", iso_time)

    def last_last_published_now_set(self) -> float:
        """set last seen time to now in both timestamp and iso format"""
        ts = datetime.now()
        self.tag_value_set("time_last_published_ts", ts.timestamp())
        self.tag_value_set("time_last_published_iso", ts.isoformat())
        return ts.timestamp()

    def publish_interval_max_exceeded(
        self, current_time: float, publish_interval_max_s: float
    ) -> bool:
        """determine if the publish interval has been exceeded"""
        last_published_ts = self.time_last_published_ts()
        if (current_time - last_published_ts) > publish_interval_max_s:
            return True
        return False
        #

    def device_name_from_id_set(self, device_id: str):
        """get device name from device_id"""
        device_name = Device.local_sensor_manager.sensor_name(device_id)
        if not device_name:
            device_name = f"UNKNOWN_DEVICE_{device_id}"
        self.tag_value_set("device_name", device_name)

    def protocol_id(self) -> str:
        """get protocol id"""
        return self.device["protocol_id"]

    def protocol_id_set(self, protocol_id: str) -> None:
        """set protocol id"""
        self.tag_value_set("protocol_id", protocol_id)

    def protocol_name(self) -> str:
        """get protocol name"""
        return self.device["protocol_name"]

    def protocol_name_set(self, protocol_name: str) -> None:
        """set protocol name"""
        self.tag_value_set("protocol_name", protocol_name)

    def protocol_description(self) -> str:
        """get protocol description"""
        return self.device["protocol_description"]

    def protocol_description_set(self, protocol_description: str) -> None:
        """set protocol description"""
        self.tag_value_set("protocol_description", protocol_description)

    def temperature_F(self) -> float:
        """get temperature in Farhenheit"""
        return self.device["temperature_F"]

    def temperature_C(self) -> float:
        """get temperature in Celcius"""
        return self.device["temperature_C"]

    def temperature_C_set(self, temperature_C: float) -> None:
        """set temperature in Celcius"""
        self.tag_value_set("temperature_C", temperature_C)

    def temperature_F_set(self, temperature_F: float) -> None:
        """set temperature in Farhenheit"""
        self.tag_value_set("temperature_F", temperature_F)

    def temperature_F_set_from_C(self, temperature_C: float) -> None:
        """set temperature in Farhenheit from Celcius"""
        temperature_F = (temperature_C * 9 / 5) + 32
        self.temperature_F_set(temperature_F)
        self.temperature_C_set(temperature_C)

    def kpa_set(self, kpa: float) -> None:
        """set kpa"""
        self.tag_value_set("pressure_kPa", kpa)

    def psi_set(self, psi: float):
        """set psi"""
        self.tag_value_set("pressure_psi", psi)

    def psi_from_kpa_set(self, kpa: float) -> None:
        """set psi from kpa"""
        psi = float(kpa) * 0.14503773773020923
        self.kpa_set(kpa)
        self.psi_set(str(psi))

    def tire_pressure(self) -> Tuple[float, float]:
        """get pressure in both kPa and psi"""
        kpa = self.device["kpa", -1]
        psi = self.device["psi", -1]
        return kpa, psi

    def device_updated(self) -> bool:
        """determine if device has been updated since last published"""
        updated = False
        last_seen = self.time_last_seen_ts()
        last_published = self.device["time_last_published_ts"]
        if last_seen > last_published:
            updated = True
        return updated

    def is_local_sensor(self) -> bool:
        """Check if this device is a local sensor"""
        return Device.local_sensor_manager.is_local_sensor(self.device_id)

    @classmethod
    def normalize_tag_name(cls, tag: str) -> str:
        """normalize tag name"""
        new_tag = attribute_map.get(tag, tag)
        if not new_tag:
            new_tag = tag
        return new_tag


# Initialize the class attribute
Device.local_sensor_manager = LocalSensorManager(
    config_dir="./config",
    sensors_file="local_sensors.json",
    check_interval=60,
)


class DeviceRegistry:
    """DeviceRegistry class to manage devices. The registry is just a
    dictionary of devices indexed by the device_id"""

    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.local_sensor_manager = Device.local_sensor_manager

    def get_device(self, device_id: str) -> Device:
        """get the device associated with the device_id;
        if the device does not exist, return a newly created device"""
        if device_id not in self.devices:
            logging.debug(
                "\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
                "DeviceRegistry: Creating new device with id %s"
                "\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n",
                device_id,
            )
            self.devices[device_id] = Device(device_id)
        return self.devices[device_id]

    # TODO: this is a duplicate of the Device method
    def update_device(self, device_id: str, tag: str, value: Any) -> None:
        device = self.get_device(device_id)
        device.tag_value_set(tag, value)
