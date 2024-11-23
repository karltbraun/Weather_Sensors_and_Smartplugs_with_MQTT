""" mqtt_config.py - MQTT Configuration Constants
    replaces mqtt_secrets.py as actual secrets are stored in environment variables
    These are default constants usually used in most scripts
"""

# MQTT Constants
MQTT_DEFAULT_PORT: int = 1883
MQTT_DEFAULT_PORT_SS: int = 8883
MQTT_DEFAULT_KEEPALIVE: int = 60
MQTT_DEFAULT_BROKER_NAME: str = "MQTT-ORG"

MQTT_DEFAULT_SUBSCRIBE_TOPICS = ["#"]
MQTT_DEFAULT_PUBLISH_TOPIC_ROOT = "test"
