# ../konductor/tests/core/test_metadata.py
"""TODO: Complete coverage for core module metadata functions."""

import pytest
from threading import Thread, Event
from modules.core.metadata import (
    MetadataSingleton,
    setup_global_metadata,
    set_global_labels,
    set_global_annotations
)
from modules.core.types import InitializationConfig, GitInfo

class TestMetadataManagement:
    @pytest.fixture
    def mock_init_config(self):
        """Fixture providing a mock initialization config."""
        return InitializationConfig(
            pulumi_config=None,
            stack_name="test-stack",
            project_name="test-project",
            default_versions={},
            git_info=GitInfo(
                commit_hash="test-hash",
                branch_name="test-branch",
                remote_url="test-url"
            ),
            metadata={
                "labels": {},
                "annotations": {}
            }
        )

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton between tests."""
        MetadataSingleton._instance = None
        yield

    def test_metadata_singleton_thread_safety(self):
        """Test thread-safe metadata singleton."""
        ready = Event()
        done = Event()

        def modify_metadata():
            ready.set()
            done.wait()
            set_global_labels({"test": "value"})

        threads = []
        for _ in range(3):
            t = Thread(target=modify_metadata)
            t.start()
            threads.append(t)
            ready.wait()
            ready.clear()

        done.set()
        for t in threads:
            t.join()

        assert MetadataSingleton().global_labels["test"] == "value"

    def test_metadata_inheritance(self, mock_init_config):
        """Test metadata inheritance from Git info."""
        setup_global_metadata(mock_init_config)
        labels = MetadataSingleton().global_labels

        assert "git.commit" in labels
        assert labels["git.commit"] == "test-hash"
        assert labels["git.branch"] == "test-branch"
        assert labels["git.repository"] == "test-url"

    def test_global_metadata_initialization(self, mock_init_config):
        """Test global metadata initialization."""
        setup_global_metadata(mock_init_config)
        metadata = MetadataSingleton()

        assert "git.commit" in metadata.global_labels
        assert metadata.global_labels["managed-by"] == "konductor"
        assert metadata.global_labels["project"] == mock_init_config.project_name
        assert metadata.global_labels["stack"] == mock_init_config.stack_name

    def test_metadata_updates(self):
        """Test metadata update operations."""
        set_global_labels({"key": "value"})
        set_global_annotations({"note": "test"})

        metadata = MetadataSingleton()
        assert metadata.global_labels["key"] == "value"
        assert metadata.global_annotations["note"] == "test"

    def test_metadata_immutability(self):
        """Test metadata immutability."""
        set_global_labels({"original": "value"})
        metadata = MetadataSingleton()

        # Try to modify returned labels
        labels = metadata.global_labels
        labels["new"] = "value"

        # Verify original wasn't modified
        assert "new" not in metadata.global_labels
        assert metadata.global_labels["original"] == "value"
