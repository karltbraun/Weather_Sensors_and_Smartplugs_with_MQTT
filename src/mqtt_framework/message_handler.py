from abc import ABC, abstractmethod
from typing import Any, Optional

from .queue_manager import MessageQueue, QueuedMessage


class BaseMessageHandler(ABC):
    """Abstract base class for message handlers"""

    def __init__(self):
        self.input_queue = MessageQueue()
        self.output_queue = MessageQueue()

    @abstractmethod
    def process_message(
        self, message: QueuedMessage
    ) -> Optional[QueuedMessage]:
        """Process a single message from the input queue"""
        pass

    @abstractmethod
    def format_message(self, message: QueuedMessage) -> dict:
        """Format message for publishing"""
        pass

    def process_queue(self):
        """Process all messages in the input queue"""
        while not self.input_queue.empty():
            message = self.input_queue.get()
            processed = self.process_message(message)
            if processed:
                self.output_queue.put(processed)
