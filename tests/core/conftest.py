# ../konductor/tests/core/conftest.py
"""TODO: Double check if this code is required and if it is complete."""
import pytest
from unittest.mock import MagicMock, patch
import pulumi
from modules.core.types import InitializationConfig, GitInfo
from modules.core.interfaces import ModuleDeploymentResult

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
        def get_bool(self, key: str, default: bool = False) -> bool:
            if "enabled" in key:
                return True
            return default

        def get_object(self, key: str, default: dict = None) -> dict:
            return default or {}

        def get(self, key: str, default: str = None) -> str:
            return default or ""

    return MockConfig()

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
        project_name="test-project",
        default_versions={},
        git_info=mock_git_info,
        metadata={"labels": {}, "annotations": {}}
    )

@pytest.fixture
def mock_module():
    """Create a mock module for testing."""
    mock = MagicMock()
    mock.deploy.return_value = ModuleDeploymentResult(
        success=True,
        version="1.0.0",
        resources=["test-resource"]
    )
    return mock

@pytest.fixture
def mock_import_module(monkeypatch, mock_module):
    """Mock importlib.import_module for testing."""
    def mock_import(name: str):
        if "error-module" in name:
            raise ImportError("Module not found")
        mock_mod = MagicMock()
        mock_mod.deploy = mock_module.deploy
        return mock_mod

    monkeypatch.setattr('importlib.import_module', mock_import)
    return mock_import

@pytest.fixture
def mock_repo():
    """Create a mock Git repository."""
    mock = MagicMock()

    # Create mock tags with version attributes
    tag1 = MagicMock()
    tag1.name = "v1.0.0"

    tag2 = MagicMock()
    tag2.name = "v1.1.0"

    tag3 = MagicMock()
    tag3.name = "v2.0.0"

    # Add tags to the mock repo
    mock.tags = [tag1, tag2, tag3]

    return mock

@pytest.fixture(autouse=True)
def cleanup_mock_modules():
    """Clean up mock modules after tests."""
    yield
    # Clean up mock modules after test
    import sys
    for module in list(sys.modules.keys()):
        if module.startswith('modules.test-module'):
            del sys.modules[module]
