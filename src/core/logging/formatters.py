# src/core/logging/formatters.py

"""Customized formatters for the logging system.

This module provides specialized formatters for different logging formats,
including:
- Standard text format
- JSON format
- Colored console output

These formatters can be used with both the Python logging system and
the Pulumi logging integration.
"""

import logging
import json
import datetime
from typing import Dict, Any, Optional


class ColoredFormatter(logging.Formatter):
    """A formatter that adds color to console output based on log level."""

    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BOLD': '\033[1m',
    }

    # Map log levels to colors
    LEVEL_COLORS = {
        logging.DEBUG: COLORS['BLUE'],
        logging.INFO: COLORS['GREEN'],
        logging.WARNING: COLORS['YELLOW'],
        logging.ERROR: COLORS['RED'],
        logging.CRITICAL: COLORS['BOLD'] + COLORS['RED'],
    }

    def __init__(self, fmt=None, datefmt=None, style='%'):
        """Initialize the formatter.

        Args:
            fmt: The format string for log messages
            datefmt: The format string for dates
            style: The style of the format string
        """
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        """Format the log record with color.

        Args:
            record: The log record to format

        Returns:
            The formatted log record with color
        """
        # Get the log level color
        level_color = self.LEVEL_COLORS.get(
            record.levelno,
            self.COLORS['RESET']
        )

        # Save the original format
        orig_format = self._style._fmt

        # Add color to the level
        colored_levelname = (
            f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        )
        record.levelname = colored_levelname

        # Format the record
        result = super().format(record)

        # Restore the original format
        self._style._fmt = orig_format

        return result


class JsonFormatter(logging.Formatter):
    """A formatter that outputs log records as JSON objects."""

    def __init__(self, additional_fields: Optional[Dict[str, Any]] = None):
        """Initialize the formatter.

        Args:
            additional_fields: Additional fields to include in every log message
        """
        super().__init__()
        self.additional_fields = additional_fields or {}

    def format(self, record):
        """Format the log record as a JSON object.

        Args:
            record: The log record to format

        Returns:
            A JSON string representation of the log record
        """
        # Get the log message from the record
        log_data = {
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }

        # Add location info if available
        if record.pathname and record.lineno:
            log_data['location'] = {
                'file': record.pathname,
                'line': record.lineno,
                'function': record.funcName,
            }

        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
            }

        # Add any additional fields
        log_data.update(self.additional_fields)

        # Add any extra fields from the record
        if hasattr(record, 'extra') and isinstance(record.extra, dict):
            log_data.update(record.extra)

        # Convert to JSON string
        return json.dumps(log_data)
