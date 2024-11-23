""" device_maps.py - maps model names to standard names """

model_map = {
    "ACURITE-606TX": "ACURITE-606TX",
    "INFACTORY-TH": "SMARTRO-SC91",
}

#
# device ID map
#   maps device_id ("id") to a specific known weather sensor
#   almost all of these will be my own devices
#

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
