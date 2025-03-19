# src/core/interfaces/logger.py

"""
Logger interface.

Defines the interface for the logging subsystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ILogger(ABC):
    """Interface for the logger.

    This interface defines the contract for logging throughout the framework.
    It provides consistent logging methods with context support.
    """

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.

        Args:
            message: Message to log
            kwargs: Additional context data
        """
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.

        Args:
            message: Message to log
            kwargs: Additional context data
        """
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.

        Args:
            message: Message to log
            kwargs: Additional context data
        """
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.

        Args:
            message: Message to log
            kwargs: Additional context data
        """
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.

        Args:
            message: Message to log
            kwargs: Additional context data
        """
        pass

    @abstractmethod
    def get_logger(self, name: str) -> 'ILogger':
        """Get a named logger.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        pass

    @abstractmethod
    def with_context(self, **context) -> 'ILogger':
        """Create a new logger with additional context.

        Args:
            context: Context data to add

        Returns:
            New logger instance with context
        """
        pass

    @abstractmethod
    def set_level(self, level: int) -> None:
        """Set the logging level.

        Args:
            level: Logging level (e.g., logging.DEBUG)
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the logger name.

        Returns:
            Logger name
        """
        pass

    @property
    @abstractmethod
    def context(self) -> Dict[str, Any]:
        """Get the current context.

        Returns:
            Context dictionary
        """
        pass
