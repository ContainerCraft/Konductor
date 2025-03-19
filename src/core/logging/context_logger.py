# src/core/logging/context_logger.py

"""Context-aware logger for the IaC framework.

This module provides a context-aware logger that can add additional
context information to log messages, such as:
- Component/module name
- Resource identifiers
- Operation context (e.g., "creating", "updating", "deleting")
- Metadata (tags, labels, annotations)

Context information is automatically added to all log messages,
making it easier to trace and filter logs.
"""

import logging
import functools
from typing import Dict, Any, Optional, Callable


class ContextLogger:
    """A context-aware logger wrapper.

    This class wraps a standard Python logger and adds contextual
    information to all log messages. It maintains the same API as
    the standard logger but enriches the messages with context.
    """

    def __init__(
        self,
        logger: logging.Logger,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize the context logger.

        Args:
            logger: The underlying Python logger to wrap.
            context: Initial context information to include in logs.
        """
        self.logger = logger
        self.context = context or {}

    def add_context(self, **kwargs) -> None:
        """Add additional context to the logger.

        Args:
            **kwargs: Context key-value pairs to add.
        """
        self.context.update(kwargs)

    def remove_context(self, *keys) -> None:
        """Remove context keys from the logger.

        Args:
            *keys: Context keys to remove.
        """
        for key in keys:
            if key in self.context:
                del self.context[key]

    def clear_context(self) -> None:
        """Clear all context information."""
        self.context.clear()

    def with_context(self, **kwargs) -> 'ContextLogger':
        """Create a new context logger with additional context.

        This method creates a new context logger with a copy of the
        current context, plus any additional context provided.

        Args:
            **kwargs: Additional context key-value pairs.

        Returns:
            A new ContextLogger instance with the combined context.
        """
        new_context = self.context.copy()
        new_context.update(kwargs)
        return ContextLogger(self.logger, new_context)

    def _format_message(self, msg: str) -> str:
        """Format a message with context information.

        Args:
            msg: The original message.

        Returns:
            The message with context information added.
        """
        if not self.context:
            return msg

        # Format the context as a string
        context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{msg} [{context_str}]"

    # Wrap standard logging methods
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message with context.

        Args:
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.debug(self._format_message(msg), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message with context.

        Args:
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.info(self._format_message(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message with context.

        Args:
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.warning(self._format_message(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message with context.

        Args:
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.error(self._format_message(msg), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message with context.

        Args:
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.critical(self._format_message(msg), *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log an exception message with context.

        Args:
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.exception(self._format_message(msg), *args, **kwargs)

    def log(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log a message with a specific level and context.

        Args:
            level: The log level.
            msg: The message to log.
            *args: Additional arguments for the logger.
            **kwargs: Additional keyword arguments for the logger.
        """
        self.logger.log(level, self._format_message(msg), *args, **kwargs)


def with_logging(logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator to add logging to a function.

    This decorator logs entry to and exit from a function, including
    parameters and return values. It also logs any exceptions raised.

    Args:
        logger: The logger to use. If None, a logger will be created
               with the name of the module containing the decorated function.

    Returns:
        The decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get or create logger
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            # Create a context logger if it's not already one
            if not isinstance(logger, ContextLogger):
                ctx_logger = ContextLogger(logger, {'function': func.__name__})
            else:
                ctx_logger = logger.with_context(function=func.__name__)

            # Log function entry
            ctx_logger.debug(f"Entering {func.__name__}")

            try:
                # Call the function
                result = func(*args, **kwargs)

                # Log function exit
                ctx_logger.debug(f"Exiting {func.__name__}")

                return result
            except Exception as e:
                # Log exception
                ctx_logger.exception(
                    f"Exception in {func.__name__}: {str(e)}"
                )
                raise
        return wrapper
    return decorator
