"""Logging configuration."""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional log format string
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
