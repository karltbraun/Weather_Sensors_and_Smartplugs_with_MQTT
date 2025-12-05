# List of things to do in the republish_processed_sensors scripts

1. Make sure environment variables for publication and subscription topics are consistent across all files:
    1. SUB_TOPIC... => MQTT_TOPIC_...
    2. PUB_TOPIC... => MQTT_TOPIC_...

2. Update to filter out sensor_id == 0.
