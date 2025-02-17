"""
Logging utility module.

Provides consistent logging configuration across the application with support for:
- Console output with colorized levels
- File output with rotation
- Different log levels for console and file handlers
- Timestamp and context information in log messages
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

# ANSI color codes for different log levels
LEVEL_COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
}


class ColorFormatter(logging.Formatter):
    """Logging formatter that adds colors to log levels in console output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors for level."""
        if record.levelname in LEVEL_COLORS:
            level_color = LEVEL_COLORS[record.levelname]
            reset_color = LEVEL_COLORS["RESET"]
            record.levelname = (
                f"{level_color}{record.levelname}{reset_color}"
            )
        return super().format(record)


def setup_logger(
    name: str,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    log_dir: Optional[Path] = None,
    max_bytes: int = 1024 * 1024,  # 1MB
    backup_count: int = 5,
    clear_existing: bool = False,
    add_timestamp: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with console and file handlers.

    Args:
        name: Logger name (typically __name__)
        console_level: Logging level for console output
        file_level: Logging level for file output
        log_dir: Directory for log files (default: project_root/logs)
        max_bytes: Maximum size of each log file
        backup_count: Number of backup files to keep
        clear_existing: Whether to clear existing log file
        add_timestamp: Whether to add timestamp to log filename

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove existing handlers
    logger.handlers = []

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    console_handler.setFormatter(ColorFormatter(console_format))
    logger.addHandler(console_handler)

    # File handler
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Add timestamp to filename if requested
    timestamp = datetime.now().strftime("%Y%m%d") if add_timestamp else ""
    log_name = f"{name}{timestamp}.log" if timestamp else f"{name}.log"
    log_file = log_dir / log_name

    if clear_existing and log_file.exists():
        log_file.unlink()

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format))
    logger.addHandler(file_handler)

    return logger


def get_logger(
    name: str, config: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        config: Optional configuration dictionary with keys:
               - console_level: Level for console output
               - file_level: Level for file output
               - clear_existing: Whether to clear log file

    Returns:
        Configured logger instance
    """
    if config is None:
        config = {}

    return setup_logger(
        name=name,
        console_level=config.get("console_level", "INFO"),
        file_level=config.get("file_level", "DEBUG"),
        clear_existing=config.get("clear_existing", False),
    )
