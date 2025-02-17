class MQTTFrameworkException(Exception):
    """Base exception for MQTT framework"""

    pass


class MQTTConnectionError(MQTTFrameworkException):
    """Raised when MQTT connection fails"""

    pass


class MessageProcessingError(MQTTFrameworkException):
    """Raised when message processing fails"""

    pass
