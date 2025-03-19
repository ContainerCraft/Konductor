# src/core/logging/log_manager.py

"""Standardized logging system that wraps Pulumi's native logging.

This module provides a unified logging interface for all modules in the framework.
It wraps Pulumi's native logging system and adds additional features like:
- Multiple log levels (standard, verbose, debug)
- Component-specific log level customization
- Standardized formatting
- Contextual logging with metadata

Usage:
    # In a module:
    from core.logging import LogManager

    # Create a logger
    log_manager = LogManager()
    logger = log_manager.get_logger("component_name")

    # Log messages
    logger.info("This is an informational message")
    logger.debug("This is a debug message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
"""

import pulumi
import logging
import sys
import json
import datetime
from typing import Dict, Any, Optional


class PulumiLogHandler(logging.Handler):
    """Custom logging handler that forwards logs to Pulumi's logging system."""

    def __init__(self, resource=None):
        """Initialize the handler.

        Args:
            resource: Optional Pulumi resource to associate logs with.
        """
        super().__init__()
        self.resource = resource

    def emit(self, record):
        """Emit a log record by forwarding it to Pulumi's logging system.

        Args:
            record: The log record to emit.
        """
        try:
            msg = self.format(record)
            level = record.levelno

            # Map Python logging levels to Pulumi logging methods
            if level >= logging.ERROR:
                pulumi.log.error(msg, resource=self.resource)
            elif level >= logging.WARNING:
                pulumi.log.warn(msg, resource=self.resource)
            elif level >= logging.INFO:
                pulumi.log.info(msg, resource=self.resource)
            elif level >= logging.DEBUG:
                pulumi.log.debug(msg, resource=self.resource)
        except Exception:
            self.handleError(record)


class LogManager:
    """Manages logging for all modules, wrapping Pulumi's native logging.

    This class provides a standardized logging interface for all modules
    in the framework. It supports multiple log levels and component-specific
    log level customization.
    """

    # Standard log level mapping
    LOG_LEVELS = {
        "standard": logging.INFO,   # Default level for normal operation
        "verbose": logging.DEBUG,  # More detailed information
        "debug": logging.DEBUG     # Very detailed debugging information
    }

    # Format strings for different environments
    LOG_FORMATS = {
        "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "json": None  # Will be converted to JSON format
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 log_level: Optional[str] = None):
        """Initialize the logging system.

        Args:
            config: Optional configuration dictionary with logging settings.
                   If not provided, default settings will be used.
            log_level: Optional log level string override. Takes precedence over
                      config. Must be one of "standard", "verbose", or "debug".
        """
        self.config = config or {}
        self.loggers: Dict[str, logging.Logger] = {}
        self.current_level = "standard"  # Default log level
        self.log_format = "default"

        # If log_level is explicitly provided, override config
        if log_level:
            self.config["level"] = log_level

        # Initialize the root logger
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure the logging system based on the configuration."""
        # Get log level from config or default to "standard"
        log_level = self.config.get("level", "standard")
        self.current_level = log_level

        # Get log format from config or default to "default"
        self.log_format = self.config.get("format", "default")

        # Determine if we should use console logging (default to False in Pulumi context)
        use_console = self.config.get("use_console", False)

        # Configure the root logger
        root_logger = logging.getLogger()

        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)

        # Set the root logger level
        python_log_level = self.LOG_LEVELS.get(log_level, logging.INFO)
        root_logger.setLevel(python_log_level)

        # Create formatter
        if self.log_format == "json":
            formatter = logging.Formatter("%(message)s")
        else:
            formatter = logging.Formatter(self.LOG_FORMATS["default"])

        # Create Pulumi handler (always needed for Pulumi context)
        pulumi_handler = PulumiLogHandler()
        pulumi_handler.setLevel(python_log_level)
        pulumi_handler.setFormatter(formatter)
        root_logger.addHandler(pulumi_handler)

        # Add console handler only if explicitly requested
        if use_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(python_log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

    def set_log_level(self, level: str) -> None:
        """Set the log level for all loggers.

        Args:
            level: The log level to set. Must be one of "standard", "verbose",
                  or "debug".
        """
        if level not in self.LOG_LEVELS:
            level = "standard"  # Default to standard if invalid level

        self.current_level = level
        python_log_level = self.LOG_LEVELS.get(level, logging.INFO)

        # Update the root logger level
        logging.getLogger().setLevel(python_log_level)

        # Update all handlers
        for handler in logging.getLogger().handlers:
            handler.setLevel(python_log_level)

        # Update all existing loggers
        for logger in self.loggers.values():
            logger.setLevel(python_log_level)

    def get_log_level(self) -> str:
        """Get the current log level name.

        Returns:
            The current log level name.
        """
        return self.current_level

    def get_log_level_value(self) -> int:
        """Get the numeric value of the current log level.

        Returns:
            The numeric log level value.
        """
        return self.LOG_LEVELS.get(self.current_level, logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name.

        Args:
            name: The name of the logger, typically the component name.

        Returns:
            A configured logger instance.
        """
        if name not in self.loggers:
            # Create a new logger
            logger_name = f"core.{name}" if not name.startswith("core.") else name
            logger = logging.getLogger(logger_name)

            # Set the logger level based on the current log level
            logger.setLevel(self.LOG_LEVELS.get(self.current_level, logging.INFO))

            # Store the logger for future reference
            self.loggers[name] = logger

        return self.loggers[name]

    def create_json_log(self, level: str, message: str, **kwargs) -> str:
        """Create a JSON-formatted log message.

        Args:
            level: The log level ("info", "warning", "error", "debug").
            message: The log message.
            **kwargs: Additional fields to include in the JSON log.

        Returns:
            A JSON-formatted log message.
        """
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message
        }

        # Add any additional fields
        log_data.update(kwargs)

        return json.dumps(log_data)
