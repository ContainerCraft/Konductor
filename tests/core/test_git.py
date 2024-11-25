# ../konductor/tests/core/test_git.py
"""TODO: Complete coverage for core module git functions."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from git import GitCommandError
from modules.core.git import (
    get_latest_semver_tag,
    get_remote_url,
    sanitize_git_info,
    extract_repo_name,
    collect_git_info
)

class TestGitUtilities:
    """Test Git integration utilities."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock Git repository."""
        mock = MagicMock()

        # Create mock tags with version attributes
        tag1, tag2, tag3 = MagicMock(), MagicMock(), MagicMock()

        # Set name attributes and make them accessible via property
        type(tag1).name = PropertyMock(return_value="v1.0.0")
        type(tag2).name = PropertyMock(return_value="v1.1.0")
        type(tag3).name = PropertyMock(return_value="v2.0.0")

        # Make tags iterable
        mock.tags = [tag1, tag2, tag3]
        return mock

    def test_get_latest_semver_tag(self, mock_repo):
        """Test semantic version tag retrieval."""
        latest = get_latest_semver_tag(mock_repo)
        assert latest == "v2.0.0"

        # Test with no valid semver tags
        mock_repo.tags = [
            MagicMock(name="not-a-version"),
            MagicMock(name="test")
        ]
        assert get_latest_semver_tag(mock_repo) is None

    def test_sanitize_git_info(self):
        """Test git info sanitization."""
        raw_info = {
            "commit": "abc123!@#",
            "branch": "feature/test-branch",
            "url": "git@github.com:org/repo.git"
        }

        sanitized = sanitize_git_info(raw_info)
        for key, value in sanitized.items():
            assert any(c.isalnum() or c in "-._" for c in value), \
                f"Invalid characters in {key}: {value}"

    def test_extract_repo_name(self):
        """Test repository name extraction."""
        test_cases = [
            ("git@github.com:org/repo.git", "org/repo"),
            ("https://github.com/org/repo.git", "org/repo"),
            ("https://github.com/org/repo", "org/repo")
        ]

        for url, expected in test_cases:
            assert extract_repo_name(url) == expected

    def test_collect_git_info_errors(self, monkeypatch):
        """Test git info collection error handling."""
        def mock_error(*args, **kwargs):
            raise Exception("Git command failed")

        monkeypatch.setattr('subprocess.check_output', mock_error)
        git_info = collect_git_info()
        assert git_info.commit_hash == "unknown"
        assert git_info.branch_name == "unknown"

    def test_get_remote_url_fallbacks(self, monkeypatch):
        """Test remote URL fallback mechanisms."""
        # Mock environment variable
        monkeypatch.setenv("CI_REPOSITORY_URL", "test-url")

        # Create a mock repo that will trigger the fallback
        mock_repo = MagicMock()
        mock_repo.remotes = []  # Empty remotes to trigger first fallback

        # Mock the git config to raise GitCommandError
        def mock_git_config(*args, **kwargs):
            raise GitCommandError("git config", "mock error")

        mock_repo.git = MagicMock()
        mock_repo.git.config = mock_git_config

        # Test the function
        url = get_remote_url(mock_repo)
        assert url == "test-url", f"Expected 'test-url' but got '{url}'"

    def test_sanitize_git_info_edge_cases(self):
        """Test git info sanitization edge cases."""
        edge_cases = {
            "empty": "",
            "special-chars": "!@#$%^&*()",
            "too-long": "a" * 100
        }

        sanitized = sanitize_git_info(edge_cases)
        for key, value in sanitized.items():
            assert len(value) <= 63, f"Value too long for {key}: {len(value)}"
            cleaned = value.replace("-", "")
            assert cleaned.isalnum() or not cleaned, \
                f"Invalid characters in {key} after cleaning: {cleaned}"
