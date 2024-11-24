# ../konductor/tests/core/test_initialization.py
import pytest
from modules.core import initialize_pulumi, InitializationConfig
from modules.core.types import GitInfo

def test_initialization_basic(monkeypatch, mock_pulumi_config):
    """Test basic initialization without any configuration."""
    monkeypatch.setattr("modules.core.initialization.get_project", lambda: "testproject")

    init_config = initialize_pulumi()

    # Verify basic configuration
    assert isinstance(init_config, InitializationConfig)
    assert init_config.project_name == "testproject"
    assert init_config.stack_name == "test-stack"

def test_initialization_git_info(mock_pulumi_config, mock_git_info):
    """Test Git information is properly initialized."""
    init_config = initialize_pulumi()

    # Verify git info
    assert isinstance(init_config.git_info, GitInfo)
    assert init_config.git_info.commit_hash == "test-hash"
    assert init_config.git_info.branch_name == "test-branch"
    assert init_config.git_info.remote_url == "test-url"

def test_initialization_metadata(mock_pulumi_config):
    """Test metadata structure is properly initialized."""
    init_config = initialize_pulumi()

    # Verify metadata structure
    assert "labels" in init_config.metadata
    assert "annotations" in init_config.metadata
    assert isinstance(init_config.metadata["labels"], dict)
    assert isinstance(init_config.metadata["annotations"], dict)
