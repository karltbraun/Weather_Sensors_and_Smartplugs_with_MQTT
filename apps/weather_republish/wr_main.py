"""
Weather Sensors Main Entry Point

Subscribes to raw sensor data, processes it, and republishes the processed data.
Uses queue-based message handling for efficient processing.
"""

import asyncio
import signal
import sys
from typing import Optional

from src.devices.weather_sensors import WeatherSensorProcessor
from src.mqtt_framework.base_client import BaseMQTTClient
from src.utils.config import load_broker_config
from src.utils.logging import setup_logger

from .config import get_app_config

topic_root = "KTBMES"
topic_source = "pi1"
topic_area = "sensors"
topic_line = "raw"
topic_prefix = f"{topic_root}/{topic_source}/{topic_area}/{topic_line}/#"


class WeatherApp:
    """Weather sensors application handler"""

    def __init__(self):
        # Initialize logging
        self.logger = setup_logger(
            name="weather_sensors",
            console_level="DEBUG",
            file_level="INFO",
            log_dir="logs",
            max_bytes=1024 * 1024,
            backup_count=3,
        )

        # Load configuration
        self.config = get_app_config()
        self.mqtt_config = load_broker_config(self.config["broker"])

        # Initialize MQTT client
        self.client = BaseMQTTClient(self.mqtt_config)
        self.processor = WeatherSensorProcessor(topic_prefix=topic_prefix)

        # Set up signal handling
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        self.running = False

    async def start(self):
        """Start the application"""
        self.logger.info("Starting Weather Sensors Application")
        self.running = True

        # Connect to broker
        try:
            await self.client.connect()

            # Subscribe to topics
            topics = self.config["topics"]
            await self.client.subscribe(topics["raw_data"])

            # Main processing loop
            while self.running:
                # Process any messages in the queue
                while not self.client.message_queue.empty():
                    message = await self.client.message_queue.get()
                    processed = self.processor.process_message(message)
                    if processed:
                        await self.client.publish(
                            topic=topics["processed_data"],
                            payload=processed.to_mqtt_payload(),
                        )

                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.running = False

    def handle_shutdown(self, signum: int, frame: Optional[object]):
        """Handle shutdown signals"""
        self.logger.info("Shutting down...")
        self.running = False

    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.disconnect()


async def main():
    """Main entry point"""
    app = WeatherApp()

    try:
        await app.start()
    except KeyboardInterrupt:
        pass
    finally:
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
