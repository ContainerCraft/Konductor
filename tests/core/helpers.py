# ../konductor/tests/core/helpers.py
"""TODO: Document what type of code belongs in this file."""
from typing import Dict, Any
from pulumi import Output

def mock_pulumi_output(value: Any) -> Output:
    """Create a mock Pulumi output value."""
    return Output.from_input(value)

def assert_resource_tags(tags: Dict[str, str], required_tags: set):
    """Verify resource tags meet requirements."""
    assert isinstance(tags, dict), "Tags must be a dictionary"
    missing_tags = required_tags - set(tags.keys())
    assert not missing_tags, f"Missing required tags: {missing_tags}"
