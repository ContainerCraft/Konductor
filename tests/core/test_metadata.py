# tests/core/test_metadata.py
def test_global_metadata():
    """Test global metadata setup."""
    init_config = mock_init_config()
    setup_global_metadata(init_config)

    # Verify metadata
    assert "git.commit" in init_config.metadata["labels"]
    assert "git.branch" in init_config.metadata["labels"]
    assert "git.remote" in init_config.metadata["labels"]
    assert "pulumi.project" in init_config.metadata["labels"]
    assert "pulumi.stack" in init_config.metadata["labels"]
