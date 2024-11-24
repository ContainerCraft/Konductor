from modules.core.config import get_enabled_modules, get_stack_outputs
from modules.core.types import InitializationConfig
from unittest.mock import MagicMock

def test_get_enabled_modules():
    """Test module enablement detection."""
    config = {
        "aws": {"enabled": True},
        "kubernetes": {"enabled": False}
    }
    enabled = get_enabled_modules(config)
    assert "aws" in enabled
    assert "kubernetes" not in enabled

def test_stack_outputs(mock_init_config: InitializationConfig):
    """Test stack output generation."""
    outputs = get_stack_outputs(mock_init_config)
    assert "compliance" in outputs
    assert "config" in outputs
    assert "k8s_app_versions" in outputs

@pytest.fixture
def mock_init_config() -> InitializationConfig:
    """Fixture for creating a mock initialization configuration."""
    mock_config = MagicMock()
    mock_git_info = MagicMock()
    return InitializationConfig(
        pulumi_config=mock_config,
        stack_name="test-stack",
        project_name="test-project",
        default_versions={},
        git_info=mock_git_info,
        metadata={"labels": {}, "annotations": {}}
    )
