# tests/unit/core/providers/test_provider_registry.py

"""Unit tests for the ProviderRegistry class."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.providers.provider_registry import ProviderRegistry


def test_provider_registry_initialization():
    """Test that the ProviderRegistry can be initialized."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Assert initialization
    assert provider_registry is not None
    assert provider_registry.logger is mock_logger
    assert provider_registry.provider_factories == {}
    assert provider_registry.providers == {}
    mock_log_manager.get_logger.assert_called_once_with("provider_registry")


def test_register_provider_factory():
    """Test registering a provider factory."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    mock_factory = MagicMock()
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Reset mock calls from initialization
    mock_logger.reset_mock()
    
    # Register a provider factory
    provider_registry.register_provider_factory("aws", mock_factory)
    
    # Verify
    assert provider_registry.provider_factories["aws"] is mock_factory
    mock_logger.info.assert_called_once_with("Registering factory for provider type: aws")


def test_create_provider_factory_exists():
    """Test creating a provider when factory exists."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    mock_provider = MagicMock()
    mock_factory = MagicMock(return_value=mock_provider)
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Register a provider factory
    provider_registry.provider_factories["aws"] = mock_factory
    
    # Reset mock calls from initialization and registration
    mock_logger.reset_mock()
    mock_factory.reset_mock()
    
    # Create a provider
    result = provider_registry.create_provider("aws", "default", region="us-west-2")
    
    # Verify
    assert result is mock_provider
    assert provider_registry.providers["aws"]["default"] is mock_provider
    mock_logger.info.assert_called_once_with("Creating provider: aws/default")
    mock_factory.assert_called_once_with(provider_name="default", region="us-west-2")


def test_create_provider_factory_not_exists():
    """Test creating a provider when factory doesn't exist."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Reset mock calls from initialization
    mock_logger.reset_mock()
    
    # Create a provider with non-existent factory
    result = provider_registry.create_provider("aws", "default")
    
    # Verify
    assert result is None
    mock_logger.info.assert_called_once_with("Creating provider: aws/default")
    mock_logger.error.assert_called_once_with("No factory registered for provider type: aws")


def test_create_provider_factory_raises_exception():
    """Test creating a provider when factory raises an exception."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    mock_factory = MagicMock(side_effect=Exception("Factory error"))
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Register a provider factory
    provider_registry.provider_factories["aws"] = mock_factory
    
    # Reset mock calls from initialization and registration
    mock_logger.reset_mock()
    
    # Create a provider
    result = provider_registry.create_provider("aws", "default")
    
    # Verify
    assert result is None
    mock_logger.info.assert_called_once_with("Creating provider: aws/default")
    mock_logger.error.assert_called_once()
    assert "Failed to create provider: aws/default" in mock_logger.error.call_args[0][0]


def test_get_provider_exists():
    """Test getting a provider that exists."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    mock_provider = MagicMock()
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Add a provider to the registry
    provider_registry.providers = {"aws": {"default": mock_provider}}
    
    # Get the provider
    result = provider_registry.get_provider("aws", "default")
    
    # Verify
    assert result is mock_provider


def test_get_provider_not_exists():
    """Test getting a provider that doesn't exist."""
    # Create mocks
    mock_log_manager = MagicMock()
    mock_logger = MagicMock()
    mock_log_manager.get_logger.return_value = mock_logger
    
    # Create the ProviderRegistry
    provider_registry = ProviderRegistry(mock_log_manager)
    
    # Get a non-existent provider
    result = provider_registry.get_provider("aws", "default")
    
    # Verify
    assert result is None
