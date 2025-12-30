"""mqtt_broker_check.py - MQTT broker connectivity verification utility.

This module provides functions to verify that an MQTT broker is accessible
before attempting to establish a full MQTT connection. It performs DNS
resolution and TCP socket connectivity checks.

Author: ktb
Updated: 2024-12-30
"""

import logging
import socket


def check_mqtt_broker_accessibility(
    host: str, port: int, timeout: float = 5.0
) -> bool:
    """Verify MQTT broker accessibility via DNS and TCP connection.

    Attempts to resolve the broker hostname and establish a TCP connection
    to verify that the broker is reachable before full MQTT client initialization.

    Args:
        host: MQTT broker hostname or IP address.
        port: MQTT broker port (typically 1883 for non-TLS, 8883 for TLS).
        timeout: Connection timeout in seconds (default: 5.0).

    Returns:
        True if broker is accessible, False otherwise.

    Logs:
        Errors are logged when DNS resolution fails or connection is refused.

    Example:
        >>> if check_mqtt_broker_accessibility('broker.example.com', 1883):
        ...     print('Broker is accessible')
    """
    try:
        resolved_ip = socket.gethostbyname(host)
    except socket.gaierror as e:
        logging.error(
            f"MQTT broker hostname resolution failed: {host} ({e})"
        )
        return False
    try:
        with socket.create_connection(
            (resolved_ip, port), timeout=timeout
        ):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        logging.error(f"MQTT broker not accessible at {host}:{port} ({e})")
        return False
        return False
