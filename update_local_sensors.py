"""
This module reads sensor configuration data from a local JSON file and publishes it to a specified MQTT topic.
It is intended for updating sensor configurations on remote devices via MQTT.

Features:
- Reads sensor configuration from 'local_sensors_update.json'.
- Connects to an MQTT broker using the paho-mqtt library.
- Publishes the configuration data to the topic defined in MQTT_TOPIC.
- Handles errors related to file reading and MQTT connection/publishing.

Usage:
Run this script directly to update the sensor configuration on the MQTT broker.
"""

import argparse
import json
import os
import sys

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

DEFAULT_INPUT_FILE = "./local_sensors_update.json"
MQTT_BROKER = os.getenv("MQTT_BROKER", "vultr2")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv(
    "MQTT_TOPIC_LOCAL_SENSORS_UPDATES",
    "KTBMES/ROSA/sensors/config/local_sensors/update",
)


def get_input_file():
    parser = argparse.ArgumentParser(
        description="Publish local sensors update to MQTT"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default=DEFAULT_INPUT_FILE,
        help=f"Path to input JSON file (default: {DEFAULT_INPUT_FILE})",
    )
    args = parser.parse_args()
    return args.input_file


def main():
    # Load environment variables from .env
    load_dotenv()

    # determine input file
    input_file = get_input_file()
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        sys.exit(1)

    # Convert payload to JSON string
    try:
        payload_str = json.dumps(payload)
    except (TypeError, ValueError) as e:
        print(f"Error serializing payload to JSON: {e}")
        print(f"input file contents:\n{payload}")
        sys.exit(1)

    # Set up MQTT client
    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(
            f"Error connecting to MQTT broker {MQTT_BROKER}:{MQTT_PORT}: {e}"
        )
        sys.exit(1)

    # Publish message
    result = client.publish(MQTT_TOPIC, payload_str)
    client.loop(0.1)  # Process network events

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Successfully published update to topic '{MQTT_TOPIC}'")
    else:
        print(f"Failed to publish update: {mqtt.error_string(result.rc)}")

    client.disconnect()


if __name__ == "__main__":
    main()
