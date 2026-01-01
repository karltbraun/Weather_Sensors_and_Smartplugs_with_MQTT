# Where we are now - 2025-12-31

We can update local_sensors via publication to KTBMES/sensors/config/local_sensors (canonical topic)
Each service publishes its current configuration to KTBMES/{PUB_SOURCE}/sensors/config/local_sensors (retained)
On startup, scripts check for the retained message on the canonical topic and use it if available,
otherwise they use the local_sensors.json file.
