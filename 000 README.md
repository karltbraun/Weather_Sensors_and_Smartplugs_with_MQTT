# Where we are now - 2025-12-22

We can update local_sensors via publication to KTBMES/sensors/config/local_sensors/updates
The current configuration is published to KTBMES/sensors/config/local_sensors/current (retained)
On startup, scripts check for the retained message on the 'current' topic and use it if available,
otherwise they use the local_sensors.json file.
