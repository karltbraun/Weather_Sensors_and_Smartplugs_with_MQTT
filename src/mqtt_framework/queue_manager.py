import time
from dataclasses import dataclass
from queue import Queue
from typing import Any


@dataclass
class QueuedMessage:
    """Message container with metadata"""

    topic: str
    payload: Any
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class MessageQueue:
    """Thread-safe message queue implementation"""

    def __init__(self):
        self._queue = Queue()

    def put(self, message: QueuedMessage):
        """Add message to queue"""
        self._queue.put(message)

    def get(self) -> QueuedMessage:
        """Get message from queue"""
        return self._queue.get()

    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()
