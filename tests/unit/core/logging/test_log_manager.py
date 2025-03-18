# tests/unit/core/logging/test_log_manager.py

"""Unit tests for the LogManager class."""

import pytest
import logging
from unittest.mock import MagicMock, patch

from src.core.logging.log_manager import LogManager


def test_log_manager_initialization():
    """Test that the LogManager can be initialized."""
    with patch('src.core.logging.log_manager.logging.getLogger') as mock_get_logger, \
         patch('src.core.logging.log_manager.logging.StreamHandler') as mock_stream_handler, \
         patch('src.core.logging.log_manager.logging.Formatter') as mock_formatter:
        
        # Setup mock logger
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        
        # Create the LogManager
        log_manager = LogManager()
        
        # Assert initialization
        assert log_manager is not None
        mock_get_logger.assert_called_once_with("core")
        mock_stream_handler.assert_called_once()
        mock_formatter.assert_called_once()
        assert mock_logger.setLevel.call_count == 1
        assert mock_logger.addHandler.call_count == 1


def test_log_manager_initialization_with_existing_handlers():
    """Test initialization when handlers already exist."""
    with patch('src.core.logging.log_manager.logging.getLogger') as mock_get_logger, \
         patch('src.core.logging.log_manager.logging.StreamHandler') as mock_stream_handler, \
         patch('src.core.logging.log_manager.logging.Formatter') as mock_formatter:
        
        # Setup mock logger with existing handlers
        mock_logger = MagicMock()
        mock_logger.handlers = [MagicMock()]  # Existing handler
        mock_get_logger.return_value = mock_logger
        
        # Create the LogManager
        log_manager = LogManager()
        
        # Assert initialization
        assert log_manager is not None
        mock_get_logger.assert_called_once_with("core")
        mock_stream_handler.assert_not_called()  # Should not create a new handler
        mock_formatter.assert_not_called()
        assert mock_logger.setLevel.call_count == 1
        assert mock_logger.addHandler.call_count == 0  # No new handler added


def test_get_logger():
    """Test getting a logger for a module or component."""
    with patch('src.core.logging.log_manager.logging.getLogger') as mock_get_logger:
        # Setup mocks
        mock_root_logger = MagicMock()
        mock_root_logger.handlers = [MagicMock()]  # Existing handler
        mock_component_logger = MagicMock()
        
        # Configure getLogger to return different loggers based on name
        def get_logger_side_effect(name):
            if name == "core":
                return mock_root_logger
            else:
                return mock_component_logger
        
        mock_get_logger.side_effect = get_logger_side_effect
        
        # Create the LogManager
        log_manager = LogManager()
        
        # Reset mock calls from initialization
        mock_get_logger.reset_mock()
        
        # Get a component logger
        component_logger = log_manager.get_logger("test_component")
        
        # Verify
        assert component_logger is mock_component_logger
        mock_get_logger.assert_called_once_with("core.test_component")


def test_log_levels_mapping():
    """Test the LOG_LEVELS mapping."""
    assert LogManager.LOG_LEVELS["debug"] == logging.DEBUG
    assert LogManager.LOG_LEVELS["info"] == logging.INFO
    assert LogManager.LOG_LEVELS["warning"] == logging.WARNING
    assert LogManager.LOG_LEVELS["error"] == logging.ERROR
    assert LogManager.LOG_LEVELS["critical"] == logging.CRITICAL
