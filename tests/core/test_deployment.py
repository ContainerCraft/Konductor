# tests/core/test_deployment.py
import pytest
from unittest.mock import MagicMock, patch
import importlib

from modules.core.deployment import DeploymentManager
from modules.core.interfaces import ModuleDeploymentResult
from modules.core.types import InitializationConfig, GitInfo

class TestDeploymentManager:
    """Test deployment orchestration."""

    @pytest.fixture
    def mock_init_config(self):
        """Create a mock initialization configuration."""
        return InitializationConfig(
            pulumi_config=MagicMock(),
            stack_name="test-stack",
            project_name="test-project",
            default_versions={},
            git_info=GitInfo(
                commit_hash="test-hash",
                branch_name="test-branch",
                remote_url="test-url"
            ),
            metadata={"labels": {}, "annotations": {}}
        )

    @pytest.fixture
    def mock_module(self):
        """Create a mock module."""
        mock = MagicMock()
        mock.deploy.return_value = ModuleDeploymentResult(
            success=True,
            version="1.0.0",
            resources=["test-resource"]
        )
        return mock

    def test_deploy_single_module(self, mock_init_config, mock_module):
        """Test successful single module deployment."""
        with patch('importlib.import_module') as mock_import:
            # Configure mock module with deploy function
            mock_deploy = MagicMock(return_value=ModuleDeploymentResult(
                success=True,
                version="1.0.0",
                resources=["test-resource"]
            ))
            mock_module.deploy = mock_deploy
            mock_import.return_value = mock_module

            manager = DeploymentManager(mock_init_config)
            result = manager.deploy_module("test-module")

            # Verify the result
            assert isinstance(result, ModuleDeploymentResult)
            assert result.success
            assert result.version == "1.0.0"
            assert "test-module" in manager.deployed_modules

    def test_deploy_module_failure(self, mock_init_config):
        """Test module deployment failure handling."""
        manager = DeploymentManager(mock_init_config)

        with patch('importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            with pytest.raises(ImportError, match="Module not found"):
                manager.deploy_module("error-module")

    def test_deploy_multiple_modules(self, mock_init_config, mock_module):
        """Test deploying multiple modules."""
        with patch('importlib.import_module') as mock_import:
            mock_import.return_value = mock_module

            manager = DeploymentManager(mock_init_config)
            modules = ["module-a", "module-b"]

            manager.deploy_modules(modules)

            assert all(m in manager.deployed_modules for m in modules)
            assert all(manager.deployed_modules[m].success for m in modules)

    def test_module_dependency_order(self, mock_init_config):
        """Test module deployment respects dependencies."""
        with patch('importlib.import_module') as mock_import:
            # Create mock modules with dependencies
            base_module = MagicMock()
            base_module.get_dependencies = MagicMock(return_value=[])
            base_module.deploy = MagicMock(return_value=ModuleDeploymentResult(
                success=True,
                version="1.0.0",
                resources=["base-resource"]
            ))

            dependent_module = MagicMock()
            dependent_module.get_dependencies = MagicMock(return_value=["base-module"])
            dependent_module.deploy = MagicMock(return_value=ModuleDeploymentResult(
                success=True,
                version="1.0.0",
                resources=["dependent-resource"]
            ))

            # Configure import to return appropriate mock
            def mock_import_side_effect(name):
                if "base-module" in name:
                    return base_module
                return dependent_module

            mock_import.side_effect = mock_import_side_effect

            manager = DeploymentManager(mock_init_config)
            modules = ["dependent-module", "base-module"]
            manager.deploy_modules(modules)

            # Verify deployment order
            deployed_order = list(manager.deployed_modules.keys())
            assert len(deployed_order) == 2
            assert deployed_order.index("base-module") < deployed_order.index("dependent-module")

    def test_deployment_error_handling(self, mock_init_config, mock_module):
        """Test deployment error handling and recovery."""
        with patch('importlib.import_module') as mock_import:
            # Configure first module to succeed, second to fail
            def mock_import_side_effect(name):
                if "good-module" in name:
                    return mock_module
                raise ImportError("Module not found")

            mock_import.side_effect = mock_import_side_effect

            manager = DeploymentManager(mock_init_config)
            modules = ["good-module", "error-module"]

            manager.deploy_modules(modules)

            assert "good-module" in manager.deployed_modules
            assert manager.deployed_modules["good-module"].success
            assert "error-module" not in manager.deployed_modules
