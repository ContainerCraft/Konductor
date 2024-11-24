# ../konductor/tests/conftest.py
import pytest
import os
from unittest.mock import patch, MagicMock
from pulumi import Config
from typing import Any
from modules.core.types import GitInfo
import pulumi

@pytest.fixture(scope="session")
def mock_pulumi_base():
    """Base Pulumi test configuration."""
    settings = {
        "project": "testproject",
        "stack": "test",
        "config": {},
        "is_test_mode": True
    }
    return settings

@pytest.fixture(autouse=True)
def mock_git_info(monkeypatch):
    """Mock Git information for testing."""
    mock_git = GitInfo(
        commit_hash="test-hash",
        branch_name="test-branch",
        remote_url="test-url"
    )

    # Mock at module level instead of function level
    monkeypatch.setattr("modules.core.git", "collect_git_info", lambda: mock_git)
    monkeypatch.setattr("modules.core.initialization.collect_git_info", lambda: mock_git)

    return mock_git

@pytest.fixture(scope="function")
def mock_environment(mock_pulumi_base, mock_git_info):
    """Setup test environment with all required mocks."""
    env_vars = {
        "PULUMI_PROJECT": mock_pulumi_base["project"],
        "PULUMI_STACK": mock_pulumi_base["stack"],
        "PULUMI_CONFIG": "{}",
        "PULUMI_TEST_MODE": "true"
    }

    # Create all required patches
    patches = [
        patch.dict(os.environ, env_vars),
        patch('pulumi.runtime.settings.get_project',
            return_value=mock_pulumi_base["project"]),
        patch('pulumi.runtime.settings.get_stack',
            return_value=mock_pulumi_base["stack"]),
        patch('pulumi.runtime.settings.is_test_mode_enabled',
            return_value=True),
        patch('modules.core.git.collect_git_info',
            return_value=mock_git_info)
    ]

    # Apply all patches
    for p in patches:
        p.start()

    yield

    # Clean up patches
    for p in patches:
        p.stop()

@pytest.fixture(autouse=True)
def mock_pulumi_config(monkeypatch):
    """Mock Pulumi configuration for testing."""
    class MockConfig:
        def get(self, key: str, default: Any = None) -> str:
            return "testproject"

        def get_bool(self, key: str, default: bool = False) -> bool:
            return False

        def get_object(self, key: str, default: Any = None) -> dict:
            return {}

    mock_config = MockConfig()

    # Mock Pulumi functions with explicit module paths
    monkeypatch.setattr("pulumi.get_project", lambda: "testproject")
    monkeypatch.setattr("pulumi.get_stack", lambda: "test-stack")
    monkeypatch.setattr("pulumi.Config", lambda *args: mock_config)

    # Also mock at the module level where it's imported
    monkeypatch.setattr("modules.core.initialization.get_project", lambda: "testproject")
    monkeypatch.setattr("modules.core.initialization.get_stack", lambda: "test-stack")

    return mock_config
