import logging
import socket


def check_mqtt_broker_accessibility(
    host: str, port: int, timeout: float = 5.0
) -> bool:
    """
    Attempt to resolve the MQTT broker hostname and connect to the specified port.
    Returns True if accessible, False otherwise. Logs errors as appropriate.
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
