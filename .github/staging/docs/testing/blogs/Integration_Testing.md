# Integration Testing Infrastructure as Code with Python and Pulumi

Integration testing validates your infrastructure code by deploying actual resources to ephemeral environments. Unlike unit tests that mock Pulumi's engine, integration tests run real deployments using the Pulumi CLI, verifying both the deployment process and resulting infrastructure.

## Why Integration Testing?

Integration testing helps ensure:

1. Infrastructure code deploys successfully
2. Configuration and secrets work correctly
3. Cloud provider interactions succeed
4. Resources are created with correct properties
5. Infrastructure behaves as expected (e.g., health checks pass)
6. Updates work from different states
7. Cleanup and resource deletion succeed

## Basic Integration Test

Here's a basic integration test for a Kubernetes namespace deployment:

```python
import pytest
from pulumi import automation as auto
from typing import Dict, Any

def create_test_stack() -> auto.Stack:
    """Create test stack for integration testing."""
    # Initialize workspace
    workspace = auto.LocalWorkspace()

    # Create stack
    stack = workspace.create_stack(
        stack_name="integration-test",
        project_name="test-project"
    )

    # Set stack configuration
    stack.set_config("kubernetes:context", auto.ConfigValue("test-cluster"))
    stack.set_config("namespace", auto.ConfigValue("test-ns"))

    return stack

def test_namespace_deployment():
    """Test full namespace deployment lifecycle."""
    stack = create_test_stack()

    try:
        # Deploy stack
        up_result = stack.up()
        assert up_result.summary.result == "succeeded"

        # Verify outputs
        outputs = up_result.outputs
        assert "namespace_name" in outputs
        assert outputs["namespace_name"].value == "test-ns"

    finally:
        # Cleanup
        stack.destroy()
        stack.workspace.remove_stack("integration-test")
```

## Validating Resource Properties

Let's extend our testing to validate specific resource properties:

```python
def test_namespace_properties():
    stack = create_test_stack()

    try:
        # Deploy infrastructure
        up_result = stack.up()

        # Get deployment resources
        resources = up_result.deployment.resources

        # Find namespace resource
        namespace = next(
            (r for r in resources
             if r.type == "kubernetes:core/v1:Namespace"),
            None
        )

        # Validate namespace properties
        assert namespace is not None, "Namespace not found"
        assert namespace.props["metadata"]["name"] == "test-ns"

        # Validate required labels
        labels = namespace.props["metadata"].get("labels", {})
        assert "environment" in labels
        assert "managed-by" in labels
        assert labels["managed-by"] == "pulumi"

    finally:
        stack.destroy()
        stack.workspace.remove_stack("integration-test")
```

## Runtime Validation

Beyond resource properties, we often need to verify the infrastructure works as expected:

```python
import requests
from kubernetes import client, config
from time import sleep

def test_service_availability():
    stack = create_test_stack()

    try:
        # Deploy infrastructure
        up_result = stack.up()

        # Get service endpoint from outputs
        endpoint = up_result.outputs["service_endpoint"].value

        # Configure kubernetes client
        config.load_kube_config()
        v1 = client.CoreV1Api()

        # Wait for service to be ready
        retries = 10
        while retries > 0:
            try:
                # Test service endpoint
                response = requests.get(f"http://{endpoint}/health")
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
                break
            except:
                retries -= 1
                sleep(5)

        # Verify pod status
        pods = v1.list_namespaced_pod(namespace="test-ns")
        assert any(
            pod.status.phase == "Running"
            for pod in pods.items
        ), "No running pods found"

    finally:
        stack.destroy()
        stack.workspace.remove_stack("integration-test")
```

## Using the Automation API

The Pulumi Automation API provides programmatic control over stack operations. Here's how to use it for integration testing:

```python
from pulumi import automation as auto
from typing import Dict, Any

class TestStack:
    """Helper class for stack management."""

    def __init__(self, stack_name: str, work_dir: str):
        self.stack_name = stack_name
        self.work_dir = work_dir
        self.workspace = auto.LocalWorkspace(work_dir=work_dir)

    def create_stack(self) -> auto.Stack:
        """Create and configure test stack."""
        # Create stack
        stack = self.workspace.create_stack(
            stack_name=self.stack_name,
            program=self._program
        )

        # Set configuration
        stack.set_config("environment", auto.ConfigValue("test"))
        return stack

    def _program(self) -> None:
        """Define infrastructure for testing."""
        import pulumi
        from pulumi_kubernetes.core.v1 import Namespace

        ns = Namespace("test-ns",
            metadata={
                "name": "test-ns",
                "labels": {
                    "environment": "test",
                    "managed-by": "pulumi"
                }
            }
        )

        pulumi.export("namespace_name", ns.metadata["name"])

def get_stack_resources(stack: auto.Stack) -> Dict[str, Any]:
    """Get resources from stack."""
    return stack.export_stack().deployment.resources
```

## Ephemeral Environments

Integration tests should use isolated environments that can be created and destroyed without affecting other infrastructure. Some best practices:

1. **Unique Names**: Use unique identifiers for stack names
   ```python
   stack_name = f"test-{int(time.time())}"
   ```

2. **Resource Isolation**: Use separate VPCs, namespaces, or resource groups
   ```python
   namespace_name = f"test-ns-{uuid.uuid4()}"
   ```

3. **Cleanup Handlers**: Ensure resources are cleaned up after tests
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_stack():
       stack = create_test_stack()
       yield stack
       stack.destroy()
       stack.workspace.remove_stack(stack.name)
   ```

4. **Configuration Management**: Use test-specific configurations
   ```python
   def configure_test_stack(stack: auto.Stack):
       stack.set_config("environment", auto.ConfigValue("test"))
       stack.set_config("resource_prefix", auto.ConfigValue("test"))
   ```

## Best Practices

1. **Test Independence**
   - Each test should create its own stack
   - Don't share resources between tests
   - Clean up all resources after tests

2. **Error Handling**
   - Always implement cleanup in finally blocks
   - Handle deployment failures gracefully
   - Add appropriate timeouts for resource creation

3. **Validation**
   - Check both resource properties and runtime behavior
   - Validate all critical configurations
   - Test both success and failure scenarios

4. **Cost Control**
   - Use smallest viable resource sizes
   - Implement test timeouts
   - Clean up resources promptly

Integration tests provide confidence that your infrastructure code works in real environments. While they take longer to run than unit tests, they catch issues that only manifest during actual deployment.
