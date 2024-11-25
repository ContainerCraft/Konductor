# ../konductor/tests/core/test_config.py
"""TODO: Evaluate for completeness."""
from modules.core.config import get_enabled_modules, get_stack_outputs
from modules.core.types import InitializationConfig, GitInfo
from unittest.mock import MagicMock
import pytest
from modules.core.config import (
    load_default_versions,
    validate_module_config,
    merge_configurations,
    initialize_config,
    get_stack_outputs
)
import json
from pulumi import Config

def test_get_enabled_modules(mock_pulumi_config):
    """Test module enablement detection."""
    enabled = get_enabled_modules(mock_pulumi_config)
    assert isinstance(enabled, list)

def test_stack_outputs(mock_init_config):
    """Test stack outputs generation."""
    outputs = get_stack_outputs(mock_init_config)

    assert isinstance(outputs, dict)
    assert "compliance" in outputs
    assert "config" in outputs
    assert "k8s_app_versions" in outputs

@pytest.fixture
def mock_init_config():
    """Create a mock initialization configuration."""
    return InitializationConfig(
        pulumi_config=Config(),
        stack_name="test-stack",
        project_name="test-project",
        default_versions={},
        git_info=GitInfo(
            commit_hash="test-hash",
            branch_name="main",
            remote_url="git@github.com:org/repo.git"
        ),
        metadata={
            "labels": {},
            "annotations": {}
        }
    )

class TestConfigManagement:
    """Test configuration management functionality."""

    def test_load_default_versions(self, tmp_path, mock_pulumi_config):
        """Test version loading from different sources."""
        version_file = tmp_path / "versions.json"
        version_file.write_text('{"test-module": "1.0.0"}')

        versions = load_default_versions(mock_pulumi_config)
        assert isinstance(versions, dict)

    def test_validate_module_config(self):
        """Test configuration validation."""
        # Test missing required fields
        config = {
            "enabled": True,
            # Missing version field
        }

        with pytest.raises(ValueError, match=r"Missing required fields: {'version'}"):
            validate_module_config("test-module", config)

        # Test valid configuration
        valid_config = {
            "enabled": True,
            "version": "1.0.0",
            "config": {}
        }

        # Should not raise an exception
        validate_module_config("test-module", valid_config)

    def test_merge_configurations(self):
        """Test configuration merging."""
        base = {"common": {"key": "value"}}
        override = {"specific": {"key": "override"}}

        result = merge_configurations(base, override)
        assert result["common"]["key"] == "value"
        assert result["specific"]["key"] == "override"
