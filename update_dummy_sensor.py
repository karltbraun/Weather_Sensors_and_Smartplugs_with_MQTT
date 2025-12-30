"""
This module provides a command-line utility to update a dummy sensor's readings via MQTT.

It prompts the user for a device ID and a temperature value in Fahrenheit, converts the temperature to Celsius,
and publishes the current timestamp, temperature in both Fahrenheit and Celsius, and a protocol identifier to
the specified MQTT broker under structured topics.

It will publish to the topic for the raw sensor data which has a topic per device attribute
(e.g., time, temperature_F, temperature_C, protocol).

Dependencies:
    - paho-mqtt

Usage:
    Run the module directly and follow the prompts to send sensor data to the MQTT broker.

Functions:
    - fahrenheit_to_celsius(f): Converts Fahrenheit to Celsius.
    - main(): Handles user input, MQTT connection, and publishing sensor data.
"""

from datetime import datetime

import paho.mqtt.client as mqtt

MQTT_BROKER = "vultr2"
MQTT_PORT = 1883
TOPIC_ROOT = "Pi1/sensors/raw"


def fahrenheit_to_celsius(f):
    """Convert temperature from Fahrenheit to Celsius.

    Args:
        f: Temperature in degrees Fahrenheit.

    Returns:
        Temperature in degrees Celsius.
    """
    return (f - 32) * 5.0 / 9.0


def main():
    """Interactive command-line tool to publish dummy sensor data via MQTT.

    Prompts user for device ID and temperature in Fahrenheit, converts to Celsius,
    and publishes sensor readings to raw sensor topics. Used for testing and
    development of sensor processing pipelines.

    Published Topics:
        <TOPIC_ROOT>/<device_id>/time: ISO timestamp
        <TOPIC_ROOT>/<device_id>/temperature_F: Temperature in Fahrenheit
        <TOPIC_ROOT>/<device_id>/temperature_C: Temperature in Celsius
        <TOPIC_ROOT>/<device_id>/protocol: Protocol ID (181 for dummy)
    """
    device_id = input("Enter device ID: ").strip()
    temp_f_str = input("Enter temperature (Fahrenheit): ").strip()
    try:
        temp_f = float(temp_f_str)
    except ValueError:
        print("Invalid temperature value.")
        return

    temp_c = round(fahrenheit_to_celsius(temp_f), 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return

    topics_payloads = [
        (f"{TOPIC_ROOT}/{device_id}/time", now_str),
        (f"{TOPIC_ROOT}/{device_id}/temperature_F", str(temp_f_str)),
        # (f"{TOPIC_ROOT}/{device_id}/temperature_C", f"{temp_c:.2f}"),
        (f"{TOPIC_ROOT}/{device_id}/temperature_C", temp_c),
        (f"{TOPIC_ROOT}/{device_id}/protocol", "91"),
    ]

    success = True
    for topic, payload in topics_payloads:
        result = client.publish(topic, payload)
        client.loop(0.1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published to {topic}: {payload}")
        else:
            print(
                f"Failed to publish to {topic}: {mqtt.error_string(result.rc)}"
            )
            success = False

    client.disconnect()
    if success:
        print("All values published successfully.")
    else:
        print("Some values failed to publish.")


if __name__ == "__main__":
    main()
