"""
ktb_logger.py

This module provides a function to set up logging for the application.
It allows configuring logging levels for both console and file handlers,
and optionally clears existing loggers.

Functions:
    ktb_logger(
        clear_logger: bool, 
        console_level: int, 
        file_level: int, 
        file_handler: str
    ) -> logging.Logger
"""

import logging


def ktb_logger(
    clear_logger: bool = False,
    console_level: int = logging.INFO,
    file_level: int = logging.ERROR,
    file_handler: str = None,
) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        clear_logger (bool): Whether to clear existing loggers.
        console_level (int): Logging level for the console handler.
        file_level (int): Logging level for the file handler.
        file_handler (str): Path to the log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger()

    if clear_logger:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    logger.setLevel(console_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)

    if file_handler:
        file_handler = logging.FileHandler(file_handler)
        file_handler.setLevel(file_level)
        logger.addHandler(file_handler)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    if file_handler:
        file_handler.setFormatter(formatter)

    return logger
