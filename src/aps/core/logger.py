"""Centralized logging configuration for Auto Penguin Setup."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """Set up logging with file rotation and appropriate console output.

    Creates a rotating log file at ~/.config/auto-penguin-setup/logs/aps.log
    with 5MB max size and 3 backup files. Console output shows INFO messages
    in normal mode and DEBUG messages in verbose mode.

    Args:
        verbose: If True, show DEBUG messages on console. Otherwise show INFO and above.

    """
    log_dir = Path.home() / ".config" / "auto-penguin-setup" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "aps.log"

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything at root level

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler with rotation (5MB, 3 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler - simple format for user-facing messages
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        Logger instance configured for the module

    """
    return logging.getLogger(name)
