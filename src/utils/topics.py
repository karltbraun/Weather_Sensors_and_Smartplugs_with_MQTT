"""
MQTT Topics utility module.

Provides functionality for handling MQTT topics including:
- Topic validation
- Topic pattern matching
- Topic construction
- Subscription topic list management
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class TopicPattern:
    """
    MQTT topic pattern with wildcards.

    Attributes:
        pattern: Topic pattern with optional wildcards (+ and #)
        description: Optional description of what the pattern matches
    """

    pattern: str
    description: Optional[str] = None

    def matches(self, topic: str) -> bool:
        """
        Check if a topic matches this pattern.

        Args:
            topic: Topic string to check

        Returns:
            True if topic matches pattern, False otherwise
        """
        pattern_parts = self.pattern.split("/")
        topic_parts = topic.split("/")

        if (
            len(pattern_parts) > len(topic_parts)
            and pattern_parts[-1] != "#"
        ):
            return False

        for p, t in zip(pattern_parts, topic_parts):
            if p == "+":
                continue
            if p == "#":
                return True
            if p != t:
                return False

        return len(pattern_parts) == len(topic_parts)


class TopicManager:
    """Manager for MQTT topics and subscriptions."""

    def __init__(self):
        """Initialize with empty topic sets."""
        self.subscriptions: Set[str] = set()
        self.patterns: List[TopicPattern] = []

    def add_subscription(self, topic: str) -> None:
        """
        Add a topic to subscribe to.

        Args:
            topic: Topic string to subscribe to

        Raises:
            ValueError: If topic format is invalid
        """
        if not self.is_valid_topic(topic):
            raise ValueError(f"Invalid topic format: {topic}")
        self.subscriptions.add(topic)

    def add_pattern(
        self, pattern: str, description: Optional[str] = None
    ) -> None:
        """
        Add a topic pattern for matching.

        Args:
            pattern: Topic pattern with optional wildcards
            description: Optional pattern description
        """
        self.patterns.append(TopicPattern(pattern, description))

    def matches_any_pattern(self, topic: str) -> bool:
        """
        Check if topic matches any stored pattern.

        Args:
            topic: Topic to check

        Returns:
            True if topic matches any pattern
        """
        return any(p.matches(topic) for p in self.patterns)

    @staticmethod
    def is_valid_topic(topic: str) -> bool:
        """
        Validate MQTT topic format.

        Args:
            topic: Topic string to validate

        Returns:
            True if topic format is valid
        """
        if not topic or len(topic) > 65535:
            return False

        # Check for invalid characters
        invalid_chars = re.compile(r"[#+\u0000]")
        if invalid_chars.search(topic):
            return False

        return True

    @staticmethod
    def build_topic(*parts: str) -> str:
        """
        Build topic string from parts.

        Args:
            parts: Topic level strings

        Returns:
            Complete topic string

        Raises:
            ValueError: If any part contains invalid characters
        """
        topic = "/".join(str(p).strip() for p in parts if p)
        if not TopicManager.is_valid_topic(topic):
            raise ValueError(f"Invalid topic: {topic}")
        return topic
