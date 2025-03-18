# tests/unit/core/config/test_config_manager.py

"""Unit tests for the ConfigManager class."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.config.config_manager import ConfigManager


def test_config_manager_initialization():
    """Test that the ConfigManager can be initialized."""
    with patch('src.core.config.config_manager.pulumi.Config') as mock_config:
        # Create the ConfigManager
        config_manager = ConfigManager()
        
        # Assert initialization
        assert config_manager is not None
        mock_config.assert_called_once()


def test_get_project_config_success():
    """Test getting project configuration when it exists."""
    with patch('src.core.config.config_manager.pulumi.Config') as mock_config:
        # Setup mock
        test_config = {"name": "test-project", "environment": "test"}
        mock_config.return_value.get_object.return_value = test_config
        
        # Create manager and get config
        config_manager = ConfigManager()
        project_config = config_manager._get_project_config()
        
        # Verify
        assert project_config == test_config
        mock_config.return_value.get_object.assert_called_once_with("project")


def test_get_project_config_fallback():
    """Test getting default project configuration when none exists."""
    with patch('src.core.config.config_manager.pulumi.Config') as mock_config:
        # Setup mock to raise exception
        mock_config.return_value.get_object.side_effect = Exception("No config found")
        
        # Create manager and get config
        config_manager = ConfigManager()
        project_config = config_manager._get_project_config()
        
        # Verify default config is returned
        assert project_config["name"] == "default-project"
        assert project_config["environment"] == "dev"


def test_get_provider_config():
    """Test getting provider configuration."""
    with patch('src.core.config.config_manager.pulumi.Config') as mock_config:
        # Create manager
        config_manager = ConfigManager()
        
        # Get provider config
        provider_config = config_manager.get_provider_config("aws")
        
        # Verify empty dict is returned in MVP
        assert provider_config == {}


def test_is_provider_enabled():
    """Test checking if a provider is enabled."""
    with patch('src.core.config.config_manager.pulumi.Config') as mock_config:
        # Create manager
        config_manager = ConfigManager()
        
        # Check if provider is enabled
        is_enabled = config_manager.is_provider_enabled("aws")
        
        # Verify False is returned in MVP
        assert is_enabled is False
