# Konductor Testing Guide

## Introduction

Testing is a critical component of the Konductor Infrastructure as Code (IaC) platform. Because Konductor uses Python with Pulumi to provision cloud resources, we can leverage both standard Python testing frameworks and Pulumi's specialized testing capabilities to ensure reliability, compliance, and correctness of our infrastructure code.

This guide provides comprehensive information about testing practices, frameworks, and implementations specific to the Konductor platform. It covers everything from basic unit tests to complex integration scenarios.

## Testing Philosophy

Konductor's testing approach is built on several key principles:

1. **Early Detection**: Catch issues during development before they reach production
2. **Comprehensive Coverage**: Test all layers from core module to infrastructure deployments
3. **Automation First**: Tests should be automated and integrated into CI/CD pipelines
4. **Type Safety**: Leverage Python's type system and Pulumi's strong typing
5. **Compliance Validation**: Ensure infrastructure meets security and compliance requirements

## Types of Testing

### Overview

Konductor supports three main types of tests:

| Test Type | Purpose | Speed | Infrastructure Required | Complexity |
|-----------|---------|-------|------------------------|------------|
| Unit Tests | Test individual components in isolation | Fast | No | Low |
| Property Tests | Validate resource properties and compliance | Medium | Yes | Medium |
| Integration Tests | Test complete infrastructure deployments | Slow | Yes | High |

### When to Use Each Type

1. **Unit Tests**
   - Testing core module functions
   - Validating configuration logic
   - Checking type safety
   - Testing resource transformations

2. **Property Tests**
   - Validating resource configurations
   - Checking compliance rules
   - Ensuring security policies
   - Validating dependencies

3. **Integration Tests**
   - Testing full deployments
   - Validating cross-resource interactions
   - Testing actual cloud behavior
   - End-to-end validation

## Setting Up the Testing Environment

### Prerequisites

1. Development Environment Setup:
   ```bash
   # Install development dependencies
   poetry install --with dev

   # Install testing tools
   poetry add --group dev pytest pytest-asyncio pytest-cov
   ```

2. Configure test settings:
   ```bash
   # Create pytest.ini
   echo """
   [pytest]
   asyncio_mode = auto
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   """ > pytest.ini
   ```

### Directory Structure

```plaintext
konductor/
├── tests/
│   ├── conftest.py                 # Shared test fixtures
│   ├── core/                       # Core module tests
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_deployment.py
│   │   └── test_metadata.py
│   ├── modules/                    # Module tests
│   │   ├── aws/
│   │   │   ├── test_deploy.py
│   │   │   └── test_config.py
│   │   └── kubernetes/
│   │       ├── test_deploy.py
│   │       └── test_config.py
│   └── integration/               # Integration tests
│       ├── test_aws_stack.py
│       └── test_k8s_stack.py
```

## Unit Testing

### Test Framework Setup

1. Create base test fixtures in `tests/conftest.py`:

```python
import pytest
import pulumi
from typing import Any, Dict

class KonductorMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        outputs = args.inputs
        if args.typ == "kubernetes:core/v1:Namespace":
            outputs = {
                **args.inputs,
                "status": {"phase": "Active"}
            }
        return [args.name + '_id', outputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}

@pytest.fixture(scope="session")
def pulumi_mocks():
    """Initialize Pulumi mocks for testing."""
    pulumi.runtime.set_mocks(KonductorMocks())

@pytest.fixture
def init_config():
    """Create a test initialization configuration."""
    from modules.core.types import InitializationConfig, GitInfo
    return InitializationConfig(
        pulumi_config={},
        stack_name="test",
        project_name="test-project",
        default_versions={},
        git_info=GitInfo(
            commit_hash="test-hash",
            branch_name="test-branch",
            remote_url="test-url"
        ),
        metadata={"labels": {}, "annotations": {}}
    )
```

### Writing Unit Tests

#### Core Module Tests

Example testing core configuration functionality:

```python
# tests/core/test_config.py
import pytest
from modules.core.config import (
    get_module_config,
    validate_module_config,
    merge_configurations
)

def test_get_module_config(pulumi_mocks):
    """Test module configuration retrieval."""
    config = {
        "enabled": True,
        "version": "1.0.0",
        "config": {
            "namespace": "test-ns"
        }
    }

    result, enabled = get_module_config(
        module_name="test-module",
        config=config,
        default_versions={"test-module": "1.0.0"}
    )

    assert enabled is True
    assert result["version"] == "1.0.0"
    assert result["config"]["namespace"] == "test-ns"

def test_validate_module_config():
    """Test configuration validation."""
    config = {
        "enabled": True,
        "version": "1.0.0",
        "config": {}
    }

    # Should not raise exceptions
    validate_module_config("test-module", config)

def test_merge_configurations():
    """Test configuration merging."""
    base = {"key1": "value1", "nested": {"sub1": "val1"}}
    override = {"key2": "value2", "nested": {"sub2": "val2"}}

    result = merge_configurations(base, override)

    assert result["key1"] == "value1"
    assert result["key2"] == "value2"
    assert result["nested"]["sub1"] == "val1"
    assert result["nested"]["sub2"] == "val2"
```

#### Testing Resource Definitions

Example testing Kubernetes namespace creation:

```python
# tests/modules/kubernetes/test_deploy.py
import pytest
import pulumi
from modules.kubernetes import deploy

@pulumi.runtime.test
def test_namespace_creation(pulumi_mocks, init_config):
    """Test namespace creation with proper metadata."""

    def check_namespace(args):
        urn, metadata = args
        assert metadata is not None, "Namespace must have metadata"
        assert "labels" in metadata, "Namespace must have labels"
        assert metadata["labels"].get("managed-by") == "konductor"

    # Deploy test namespace
    ns = deploy.create_namespace(
        name="test-ns",
        init_config=init_config
    )

    return pulumi.Output.all(ns.urn, ns.metadata).apply(check_namespace)

@pulumi.runtime.test
def test_namespace_validation(pulumi_mocks):
    """Test namespace name validation."""
    with pytest.raises(ValueError):
        deploy.create_namespace(name="invalid/name")
```

### Testing Best Practices

1. **Isolation**
   - Each test should be independent
   - Use fixtures for common setup
   - Clean up resources after tests

2. **Mocking**
   - Mock external services and APIs
   - Provide realistic mock responses
   - Test edge cases and errors

3. **Assertions**
   - Use specific assertions
   - Check both positive and negative cases
   - Validate resource properties

4. **Resource Testing**
   - Test resource creation parameters
   - Validate metadata and tags
   - Check compliance rules

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/core/test_config.py

# Run with coverage
poetry run pytest --cov=modules

# Generate coverage report
poetry run pytest --cov=modules --cov-report=html
```

### Test Coverage Requirements

Konductor maintains strict test coverage requirements:

1. **Core Module**: Minimum 90% coverage
2. **Infrastructure Modules**: Minimum 80% coverage
3. **Helper Functions**: Minimum 85% coverage

Coverage is enforced through CI/CD pipelines and must be maintained for all pull requests.
