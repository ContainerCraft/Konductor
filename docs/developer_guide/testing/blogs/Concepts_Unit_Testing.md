# Unit Testing Pulumi Programs

## Introduction

Pulumi programs leverage Python with Pulumi libraries to define and manage infrastructure. When developing modules and infrastructure code, you can use Python's full testing capabilities along with Pulumi's testing framework.

During normal operation, your program is executed with Pulumi's CLI to deploy infrastructure. For unit testing, we intercept this communication using mocks, which simulate responses within the same process and return test data for each call.

This mock-based approach offers several advantages:
- Fast execution since no real infrastructure is provisioned
- Deterministic results independent of external systems
- Ability to test edge cases and failure scenarios

## Getting Started

Let's create a test suite for a Konductor specific Pulumi infrastructure-as-code module. We'll use an example that deploys Kubernetes resources to demonstrate Konductor's testing patterns.

### Sample Module

Here's a simple Kubernetes namespace module we want to test:

```python
# modules/kubernetes/namespaces/deploy.py
from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import Namespace
from modules.core import InitializationConfig

def create_namespace(
    name: str,
    init_config: InitializationConfig
) -> Namespace:
    """Create a Kubernetes namespace with Konductor metadata."""

    # Create namespace without required metadata
    return Namespace(
        name,
        metadata={
            "name": name
        },
        opts=ResourceOptions(
            provider=init_config.kubernetes_provider
        )
    )
```

We want to test that:
1. Namespaces have required Konductor metadata labels
2. Namespace names follow naming conventions
3. Resource options are properly configured

### Adding Test Mocks

First, let's create mocks for Konductor's Pulumi interactions:

```python
# tests/kubernetes/test_namespaces.py
import pulumi
from modules.core.types import InitializationConfig, GitInfo

class KonductorMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        # Create mock outputs matching inputs
        outputs = args.inputs

        # Add mock data for Kubernetes resources
        if args.typ == "kubernetes:core/v1:Namespace":
            outputs = {
                **args.inputs,
                "status": {"phase": "Active"}
            }

        return [args.name + '_id', outputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}

# Configure mocks before importing modules
pulumi.runtime.set_mocks(KonductorMocks())
```

### Writing the Tests

Now we can write our tests using Pulumi testing patterns:

```python
import pytest
from modules.kubernetes.namespaces import create_namespace
from modules.core import InitializationConfig, GitInfo

# Setup test fixtures
@pytest.fixture
def init_config():
    """Create test initialization config."""
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

# Test 1: Verify namespace metadata
@pulumi.runtime.test
def test_namespace_metadata(init_config):
    def check_metadata(args):
        urn, metadata = args

        # Check required labels exist
        labels = metadata.get("labels", {})
        assert "managed-by" in labels, f"namespace {urn} missing managed-by label"
        assert "environment" in labels, f"namespace {urn} missing environment label"

        # Verify label values
        assert labels["managed-by"] == "pulumi", "incorrect managed-by label"

    # Create test namespace
    ns = create_namespace("test-ns", init_config)

    return pulumi.Output.all(ns.urn, ns.metadata).apply(check_metadata)

# Test 2: Verify namespace naming
@pulumi.runtime.test
def test_namespace_naming():
    with pytest.raises(ValueError):
        create_namespace("invalid/name", init_config)

# Test 3: Verify resource options
@pulumi.runtime.test
def test_namespace_options(init_config):
    def check_options(args):
        urn, opts = args
        assert opts.provider is not None, "provider not configured"

    ns = create_namespace("test-ns", init_config)
    return pulumi.Output.all(ns.urn, ns.__dict__["opts"]).apply(check_options)
```

Important points about these tests:

1. **Asynchronous Testing**: Use `@pulumi.runtime.test` for handling Pulumi's async outputs.
2. **Output Handling**: Access resource properties using `pulumi.Output.all()` and `.apply()`.
3. **Mock Limitations**: Some provider-computed values won't be available unless explicitly mocked.
4. **Konductor Context**: Tests use `InitializationConfig` and other existing Konductor IaC types.

### Running the Tests

Execute tests using pytest:

```bash
poetry run pytest tests/kubernetes/test_namespaces.py -v
```

### Fixing the Implementation

If tests fail, update the module implementation:

```python
# modules/kubernetes/namespaces/deploy.py
from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import Namespace
from modules.core import InitializationConfig
import re

def create_namespace(
    name: str,
    init_config: InitializationConfig
) -> Namespace:
    """Create a Kubernetes namespace with Pulumi metadata."""

    # Validate namespace name
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', name):
        raise ValueError("Invalid namespace name")

    # Create namespace with required metadata
    return Namespace(
        name,
        metadata={
            "name": name,
            "labels": {
                "managed-by": "pulumi",
                "environment": init_config.stack_name,
                **init_config.metadata.get("labels", {})
            },
            "annotations": init_config.metadata.get("annotations", {})
        },
        opts=ResourceOptions(
            provider=init_config.kubernetes_provider
        )
    )
```

Now when you run the tests again, they should pass:

```
============================= test session starts ==============================
collected 3 items

tests/kubernetes/test_namespaces.py::test_namespace_metadata PASSED [ 33%]
tests/kubernetes/test_namespaces.py::test_namespace_naming PASSED    [ 66%]
tests/kubernetes/test_namespaces.py::test_namespace_options PASSED   [100%]

============================== 3 passed in 0.12s ==============================
```

This example demonstrates how to:
- Write unit tests for Konductor modules
- Use Konductor's testing patterns and utilities
- Mock Pulumi resources in a Konductor IaC context
- Test both success and failure cases
- Validate specific requirements

For more examples and patterns, see the core module tests in `tests/core/` and other module tests in the `tests/` directory.
