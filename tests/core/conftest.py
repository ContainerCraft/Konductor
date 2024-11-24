# ../konductor/tests/core/conftest.py
import pytest
from unittest.mock import MagicMock
import pulumi
from modules.core.types import InitializationConfig, GitInfo
from typing import Any

class KonductorMocks(pulumi.runtime.Mocks):
    """Mock Pulumi runtime for testing."""
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + '_id', args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}

@pytest.fixture(scope="session", autouse=True)
def setup_pulumi_mocks():
    """Set up Pulumi mocks for all tests."""
    pulumi.runtime.set_mocks(KonductorMocks())

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

@pytest.fixture(autouse=True)
def mock_git_info(monkeypatch):
    """Mock Git information for testing."""
    # Mock subprocess.check_output
    def mock_check_output(cmd, *args, **kwargs):
        if cmd[0] == 'git':
            if cmd[1] == 'rev-parse' and cmd[2] == 'HEAD':
                return b'test-hash\n'
            elif cmd[1] == 'rev-parse' and cmd[2] == '--abbrev-ref':
                return b'test-branch\n'
            elif cmd[1] == 'config':
                return b'test-url\n'
        return b''

    monkeypatch.setattr('subprocess.check_output', mock_check_output)

    mock_git = GitInfo(
        commit_hash="test-hash",
        branch_name="test-branch",
        remote_url="test-url"
    )
    return mock_git

@pytest.fixture
def mock_init_config(mock_pulumi_config, mock_git_info):
    """Create a mock initialization configuration."""
    return InitializationConfig(
        pulumi_config=mock_pulumi_config,
        stack_name="test-stack",
        project_name="testproject",
        default_versions={},
        git_info=mock_git_info,
        metadata={"labels": {}, "annotations": {}}
    )
