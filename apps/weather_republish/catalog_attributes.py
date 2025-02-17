import csv
import json
import signal
from collections import defaultdict
from datetime import datetime
from typing import DefaultDict, Dict, Set

import paho.mqtt.client as mqtt

# Global variables for storing device attributes
device_protocols: Dict[str, str] = {}  # Maps device_id to protocol_id
protocol_matrix: DefaultDict[str, Set[str]] = defaultdict(set)
running = True


def save_matrix_to_file(filename: str = "protocol_attributes.csv"):
    """Save the protocol attribute matrix to a CSV file."""
    # Get all unique attributes across all protocols
    all_attributes = set()
    for attributes in protocol_matrix.values():
        all_attributes.update(attributes)

    # Sort attributes for consistent output
    sorted_attributes = sorted(all_attributes)

    # Create the matrix for writing
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        # Write header row with attributes
        writer.writerow(["Protocol ID"] + sorted_attributes)

        # Write each protocol's row
        for protocol_id in sorted(protocol_matrix.keys()):
            row = [protocol_id]
            for attr in sorted_attributes:
                # Put 'X' if attribute exists for protocol, empty string if not
                row.append(
                    "X" if attr in protocol_matrix[protocol_id] else ""
                )
            writer.writerow(row)


def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Connected with result code {rc}")
    client.subscribe("KTBMES/pi1/sensors/raw/#")


def on_message(client, userdata, msg):
    """Callback for when a message is received from the broker."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Parse topic structure: KTBMES/pi1/sensors/raw/<device_id>/<attribute>
        topic_parts = msg.topic.split("/")
        if len(topic_parts) >= 6:
            device_id = topic_parts[4]
            attribute = topic_parts[5]

            # If this is a protocol message, update the device's protocol mapping
            if attribute == "protocol":
                protocol_id = msg.payload.decode()
                device_protocols[device_id] = protocol_id

            # Only add attributes if we know the device's protocol
            if device_id in device_protocols:
                protocol_id = device_protocols[device_id]
                protocol_matrix[protocol_id].add(attribute)

            # Debug print
            print(
                f"[{timestamp}] Device {device_id} (Protocol {device_protocols.get(device_id, 'unknown')}): "
                f"{attribute} = {msg.payload.decode()}"
            )

    except Exception as e:
        print("!" * 75)
        print(f"[{timestamp}] Error processing message: {str(e)}")
        print(f"[{timestamp}] Topic: {msg.topic}")
        print(f"[{timestamp}] Payload: {msg.payload}")
        print("!" * 75)


def handle_signal(signum, frame):
    """Signal handler for graceful shutdown."""
    global running
    print(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    )
    print("Received signal to terminate. Saving data and shutting down...")
    print(
        "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    )
    running = False


def main():
    """Main function to run the MQTT client and monitor messages."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Set up MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to broker
    broker_config = {"host": "n-vultr1", "port": 1883, "keepalive": 60}

    try:
        client.connect(**broker_config)
    except Exception as e:
        print(f"Failed to connect to broker: {e}")
        return

    # Start the loop
    client.loop_start()

    # Keep running until signal is received
    while running:
        pass

    # Clean up
    client.loop_stop()
    client.disconnect()

    # Save the matrix to file
    save_matrix_to_file()
    print("Matrix saved to protocol_attributes.csv")


if __name__ == "__main__":
    main()
