import logging
from datetime import datetime
from typing import Any, Dict

# TODO: this should be read in from a json file like we do for some of the other
# TODO: maps.  Dynamically checked and read in when changed.
model_map = {
    """ device_maps.py - maps model names to standard names """
    "ACURITE-606TX": "ACURITE-606TX",
    "INFACTORY-TH": "SMARTRO-SC91",
}

#
# device ID map
#   maps device_id ("id") to a specific known weather sensor
#   almost all of these will be my own devices
#

# TODO: this should be read in from a json file like we do for some of the other
# TODO: maps.  Dynamically checked and read in when changed.

my_sensors_id_map = {
    "79": {  # confirmed with heater test 2024-02-02
        "id_sensor_name": "SC91-A",
        "sensor_name": "OFC-A",
    },
    "167": {  # confirmed with heater test 2024-02-03
        "id_sensor_name": "SC91-B",
        "sensor_name": "PATIO-B",
    },
    "211": {
        "id_sensor_name": "SC91-C",
        "sensor_name": "PATIO-C",
    },
    "37": {
        "id_sensor_name": "SC91-C",
        "sensor_name": "PATIO-C",
    },
    "49": {
        "id_sensor_name": "ACRT-01",
        "sensor_name": "BRZWY-ACRT",
    },
    "98": {
        "id_sensor_name": "ACRT-02",
        "sensor_name": "PORCH-ACRT",
    },
    "132": {
        "id_sensor_name": "ACRT-02",
        "sensor_name": "PORCH-ACRT",
    },
    "200": {
        "id_sensor_name": "ACRT-02",
        "sensor_name": "PORCH-ACRT?",
    },
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
    def __init__(self, device_id):
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
            "time_last_published_ts": 0,
            "time_last_published_iso": "NEVER",
        }

    def __str__(self):
        return str(self.device)

    def tag_value(self, tag) -> Any:
        """get tag value"""
        return self.device.get(tag, None)

    def tag_value_set(self, tag, value):
        """set tag value and update last seen time"""
        if tag not in self.device:
            logging.info(
                "\ntag_value_set: Adding tag %s with value %s to device with id %s\n",
                tag,
                value,
                self.device["device_id"],
            )
        self.device[tag] = value

    def device_name(self):
        """get device name"""
        return self.device["device_name"]

    def device_name_set(self, device_name):
        """set device name"""
        self.tag_value_set("device_name", device_name)

    def time_last_seen_ts(self):
        """get last seen time"""
        return self.device["time_last_seen_ts"]

    def time_last_seen_ts_set(self, timestamp):
        """set last seen time"""
        self.tag_value_set("time_last_seen_ts", timestamp)

    def time_last_seen_iso(self):
        """get last seen time in iso format"""
        return self.device["time_last_seen_iso"]

    def time_last_seen_iso_set(self, iso_time):
        """set last seen time in iso format"""
        self.tag_value_set("time_last_seen_iso", iso_time)

    def last_last_seen_now_set(self):
        """set last seen time to now"""
        ts = datetime.now()
        self.time_last_seen_ts_set(ts.timestamp())
        self.time_last_seen_iso_set(ts.isoformat())
        return ts.timestamp()

        #

    def time_last_published_ts(self):
        """get last seen time"""
        return self.device["time_last_published_ts"]

    def time_last_published_ts_set(self, timestamp):
        """set last seen time"""
        self.tag_value_set("time_last_published_ts", timestamp)

    def time_last_published_iso(self):
        """get last seen time in iso format"""
        return self.device["time_last_published_iso"]

    def time_last_published_iso_set(self, iso_time):
        """set last seen time in iso format"""
        self.tag_value_set("time_last_published_iso", iso_time)

    def last_last_published_now_set(self):
        """set last seen time to now"""
        ts = datetime.now()
        self.tag_value_set("time_last_published_ts", ts.timestamp())
        self.tag_value_set("time_last_published_iso", ts.isoformat())
        return ts.timestamp()

        #

    def device_name_from_id_set(self, device_id: str):
        """get device name from device_id"""
        device_info = my_sensors_id_map.get(device_id, {})
        device_name = device_info.get(
            "sensor_name", f"UNKNOWN_{device_id}"
        )
        # TODO: Do we need to check for error?
        self.tag_value_set("device_name", device_name)

    def protocol_id(self):
        """get protocol id"""
        return self.device["protocol_id"]

    def protocol_id_set(self, protocol_id):
        """set protocol id"""
        self.tag_value_set("protocol_id", protocol_id)

    def protocol_name(self):
        """get protocol name"""
        return self.device["protocol_name"]

    def protocol_name_set(self, protocol_name):
        """set protocol name"""
        self.tag_value_set("protocol_name", protocol_name)

    def protocol_description(self):
        """get protocol description"""
        return self.device["protocol_description"]

    def protocol_description_set(self, protocol_description):
        """set protocol description"""
        self.tag_value_set("protocol_description", protocol_description)

    def temperature_F(self):
        """get temperature in Farhenheit"""
        return self.device["temperature_F"]

    def temperature_C(self):
        """get temperature in Celcius"""
        return self.device["temperature_C"]

    def temperature_C_set(self, temperature_C):
        """set temperature in Celcius"""
        self.tag_value_set("temperature_C", temperature_C)

    def temperature_F_set(self, temperature_F):
        """set temperature in Farhenheit"""
        self.tag_value_set("temperature_F", temperature_F)

    def temperature_F_set_from_C(self, temperature_C):
        """set temperature in Farhenheit from Celcius"""
        temperature_F = (temperature_C * 9 / 5) + 32
        self.temperature_F_set(temperature_F)
        self.temperature_C_set(temperature_C)

    def kpa_set(self, kpa):
        """set kpa"""
        self.tag_value_set("pressure_kPa", kpa)

    def psi_set(self, psi):
        """set psi"""
        self.tag_value_set("pressure_psi", psi)

    def psi_from_kpa_set(self, kpa):
        """set psi from kpa"""
        psi = int(kpa) * 0.14503773773020923
        self.kpa_set(kpa)
        self.psi_set(str(psi))

    def tire_pressure(self):
        """get pressure in both kPa and psi"""
        kpa = self.device["kpa", -1]
        psi = self.device["psi", -1]
        return kpa, psi

    def device_updated(self):
        """determine if device has been updated since last published"""
        updated = False
        last_seen = self.time_last_seen_ts()
        last_published = self.device["time_last_published_ts"]
        if last_seen > last_published:
            updated = True
        return updated

    @classmethod
    def normalize_tag_name(cls, tag):
        """normalize tag name"""
        new_tag = attribute_map.get(tag, tag)
        if not new_tag:
            new_tag = tag
        return new_tag


class DeviceRegistry:
    """DeviceRegistry class to manage devices. The registry is just a
    dictionary of devices indexed by the device_id"""

    def __init__(self):
        self.devices: Dict[str, Device] = {}

    def get_device(self, device_id: str) -> Device:
        """get the device associated with the device_id;
        if the device does not exist, return a newly created device"""
        if device_id not in self.devices:
            self.devices[device_id] = Device(device_id)
        return self.devices[device_id]

    # TODO: this is a duplicate of the Device method
    def update_device(self, device_id: str, tag: str, value: Any) -> None:
        device = self.get_device(device_id)
        device.tag_value_set(tag, value)
