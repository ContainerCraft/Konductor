# tests/unit/core/test_module.py

"""Unit tests for the CoreModule class."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.module import CoreModule


def test_core_module_initialization():
    """Test that the CoreModule can be initialized."""
    # Mock the dependencies
    with patch('src.core.module.LogManager') as mock_log_manager, \
         patch('src.core.module.ConfigManager') as mock_config_manager, \
         patch('src.core.module.ProviderDiscovery') as mock_provider_discovery, \
         patch('src.core.module.ProviderRegistry') as mock_provider_registry:
        
        # Setup mock returns
        mock_log_manager.return_value.get_logger.return_value = MagicMock()
        
        # Create the CoreModule
        core_module = CoreModule()
        
        # Assert that the module was initialized correctly
        assert core_module is not None
        assert core_module.log_manager is not None
        assert core_module.config_manager is not None
        assert core_module.provider_discovery is not None
        assert core_module.provider_registry is not None
        
        # Verify method calls
        mock_log_manager.assert_called_once()
        mock_config_manager.assert_called_once()
        mock_provider_discovery.assert_called_once_with(core_module.log_manager)
        mock_provider_registry.assert_called_once_with(core_module.log_manager)
        

def test_core_module_run():
    """Test that the CoreModule run method works correctly."""
    # Mock the dependencies
    with patch('src.core.module.LogManager') as mock_log_manager, \
         patch('src.core.module.ConfigManager') as mock_config_manager, \
         patch('src.core.module.ProviderDiscovery') as mock_provider_discovery, \
         patch('src.core.module.ProviderRegistry') as mock_provider_registry, \
         patch('src.core.module.pulumi') as mock_pulumi:
        
        # Setup mock returns
        mock_logger = MagicMock()
        mock_log_manager.return_value.get_logger.return_value = mock_logger
        
        # Create the CoreModule
        core_module = CoreModule()
        
        # Reset mock calls from initialization
        mock_logger.reset_mock()
        mock_pulumi.reset_mock()
        
        # Run the core module
        core_module.run()
        
        # Verify the run method behavior
        assert mock_logger.info.call_count >= 2  # At least two info logs
        assert mock_pulumi.export.call_count >= 1  # At least one export call
