# src/core/logging/log_manager.py

"""Logging system for the core module."""

import logging
import sys
from typing import Dict, Any, Optional

class LogManager:
    """Manages logging for all modules, wrapping Python's native logging system."""

    # Log levels mapping
    LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self, log_level: str = "info"):
        """Initialize the logging system.

        Args:
            log_level: The log level to use. Defaults to "info".
        """
        # Initialize the root logger
        self.root_logger = logging.getLogger("core")
        self.root_logger.setLevel(self.LOG_LEVELS.get(log_level, logging.INFO))

        # If no handlers exist, add a console handler
        if not self.root_logger.handlers:
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)

            # Add handler to logger
            self.root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger for a specific module or component.

        Args:
            name: The name of the module or component.

        Returns:
            A configured Logger instance.
        """
        logger = logging.getLogger(f"core.{name}")
        return logger
