# ../konductor/tests/core/test_integration.py
"""TODO: Complete coverage for core module integration tests."""

import pytest
from modules.core import initialize_pulumi, DeploymentManager
from modules.core.metadata import setup_global_metadata
from modules.core.config import merge_configurations, get_module_config, validate_module_config

class TestCoreIntegration:
    """Test core module integration scenarios."""

    async def test_full_deployment_cycle(self, mock_init_config):
        """Test complete deployment lifecycle."""
        # Initialize
        init_config = initialize_pulumi()
        setup_global_metadata(init_config)

        # Create a mock test module for testing
        import sys
        from unittest.mock import MagicMock
        from modules.core.interfaces import ModuleDeploymentResult

        # Create mock modules
        mock_module = MagicMock()
        mock_module.deploy.return_value = ModuleDeploymentResult(
            success=True,
            version="1.0.0",
            resources=["test-resource"]
        )

        # Add mock modules to sys.modules
        sys.modules['modules.test-module-a.deploy'] = mock_module
        sys.modules['modules.test-module-b.deploy'] = mock_module

        # Deploy
        manager = DeploymentManager(init_config)
        modules = ["test-module-a", "test-module-b"]

        manager.deploy_modules(modules)

        # Verify
        assert all(
            m in manager.deployed_modules and
            manager.deployed_modules[m].success
            for m in modules
        )

    async def test_configuration_inheritance(self, mock_init_config):
        """Test configuration inheritance and merging."""
        base_config = {"common": {"setting": "value"}}
        override_config = {"module-specific": {"setting": "override"}}

        # Test configuration merging
        result = merge_configurations(base_config, override_config)
        assert result["common"]["setting"] == "value"
        assert result["module-specific"]["setting"] == "override"

    async def test_resource_metadata_propagation(self, mock_init_config):
        """Test metadata propagation to resources."""
        init_config = initialize_pulumi()
        setup_global_metadata(init_config)

        # Create mock module
        import sys
        from unittest.mock import MagicMock
        from modules.core.interfaces import ModuleDeploymentResult

        mock_module = MagicMock()
        mock_module.deploy.return_value = ModuleDeploymentResult(
            success=True,
            version="1.0.0",
            resources=["test-resource"],
            metadata={
                "git.commit": init_config.git_info.commit_hash,
                "managed-by": "konductor"
            }
        )

        # Add mock module to sys.modules
        sys.modules['modules.test-module.deploy'] = mock_module

        # Deploy test module
        manager = DeploymentManager(init_config)
        result = manager.deploy_module("test-module")

        # Verify metadata propagation
        assert result.metadata["git.commit"] == init_config.git_info.commit_hash
        assert result.metadata["managed-by"] == "konductor"

    async def test_configuration_validation_pipeline(self, mock_init_config):
        """Test complete configuration validation pipeline."""
        # Test configuration loading with required fields
        config = {
            "enabled": True,  # Add required enabled field
            "version": "1.0.0",
            "config": {}
        }

        # Validate configuration
        validate_module_config("test-module", config)

        # Test deployment with validated config
        manager = DeploymentManager(mock_init_config)

        # Create and inject mock module
        import sys
        from unittest.mock import MagicMock
        from modules.core.interfaces import ModuleDeploymentResult

        mock_module = MagicMock()
        mock_module.deploy.return_value = ModuleDeploymentResult(
            success=True,
            version="1.0.0",
            resources=["test-resource"]
        )
        sys.modules['modules.test-module.deploy'] = mock_module

        result = manager.deploy_module("test-module")

        assert result.success
