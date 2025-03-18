# tests/unit/core/providers/test_provider_discovery.py

"""Unit tests for the ProviderDiscovery class."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.providers.provider_discovery import ProviderDiscovery


def test_provider_discovery_initialization():
    """Test that the ProviderDiscovery can be initialized."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    
    # Create the ProviderDiscovery
    provider_discovery = ProviderDiscovery(mock_log_manager)
    
    # Assert initialization
    assert provider_discovery is not None
    assert provider_discovery.logger is mock_logger
    assert provider_discovery.provider_modules == {}
    mock_log_manager.get_logger.assert_called_once_with("provider_discovery")


def test_discover_provider_modules():
    """Test discovering provider modules."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    
    # Create the ProviderDiscovery
    provider_discovery = ProviderDiscovery(mock_log_manager)
    
    # Reset mock calls from initialization
    mock_logger.reset_mock()
    
    # Discover provider modules
    discovered_modules = provider_discovery.discover_provider_modules()
    
    # Verify
    assert discovered_modules == []  # Empty list in MVP
    mock_logger.info.assert_called_once_with("Discovering provider modules")


def test_get_provider_modules():
    """Test getting provider modules."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    
    # Create the ProviderDiscovery
    provider_discovery = ProviderDiscovery(mock_log_manager)
    
    # Get provider modules
    provider_modules = provider_discovery.get_provider_modules()
    
    # Verify
    assert provider_modules == {}  # Empty dict in MVP
