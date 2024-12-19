## Integration Testing

### Overview

Integration tests in Konductor deploy actual infrastructure to verify the complete deployment process and resource interactions. These tests are designed to validate end-to-end functionality in real cloud environments.

### Setup and Configuration

#### Directory Structure

```plaintext
konductor/
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── stacks/
│   │   │   ├── test_stack.py
│   │   │   └── test_configs/
│   │   ├── scenarios/
│   │   │   ├── test_aws_deployment.py
│   │   │   └── test_kubernetes_deployment.py
│   │   └── validation/
│   │       ├── aws_validators.py
│   │       └── kubernetes_validators.py
```

#### Test Configuration

```python
# tests/integration/conftest.py
import pytest
import pulumi
from pulumi import automation as auto

@pytest.fixture(scope="module")
def test_stack():
    """Create a test stack for integration testing."""
    stack = auto.create_or_select_stack(
        stack_name="integration-test",
        project_name="konductor-test",
        program=lambda: None
    )

    # Set stack configuration
    stack.set_config("aws:region", auto.ConfigValue("us-west-2"))
    stack.set_config(
        "kubernetes:context",
        auto.ConfigValue("test-cluster")
    )

    yield stack

    # Cleanup
    stack.destroy()
    stack.workspace.remove_stack("integration-test")

@pytest.fixture
def aws_client():
    """Create AWS client for validation."""
    import boto3
    return boto3.client('ec2')

@pytest.fixture
def kubernetes_client():
    """Create Kubernetes client for validation."""
    from kubernetes import client, config
    config.load_kube_config()
    return client.CoreV1Api()
```

### Writing Integration Tests

#### Stack Deployment Tests

```python
# tests/integration/scenarios/test_aws_deployment.py
import pytest
from pulumi import automation as auto

def test_aws_infrastructure_deployment(test_stack, aws_client):
    """Test complete AWS infrastructure deployment."""
    # Deploy stack
    up_result = test_stack.up()

    # Get outputs
    outputs = up_result.outputs

    # Validate VPC creation
    vpc_id = outputs["vpc_id"].value
    vpc = aws_client.describe_vpcs(VpcIds=[vpc_id])
    assert vpc["Vpcs"], "VPC not found"

    # Validate subnet creation
    subnet_ids = outputs["subnet_ids"].value
    subnets = aws_client.describe_subnets(
        SubnetIds=subnet_ids
    )
    assert len(subnets["Subnets"]) == 3, "Missing subnets"

    # Validate security groups
    sg_id = outputs["security_group_id"].value
    sg = aws_client.describe_security_groups(
        GroupIds=[sg_id]
    )
    assert sg["SecurityGroups"], "Security group not found"

def test_aws_resource_tags(test_stack, aws_client):
    """Test AWS resource tagging."""
    outputs = test_stack.outputs()

    # Check VPC tags
    vpc_id = outputs["vpc_id"].value
    vpc = aws_client.describe_vpcs(VpcIds=[vpc_id])
    tags = {t["Key"]: t["Value"] for t in vpc["Vpcs"][0]["Tags"]}

    assert tags["Environment"] == "test"
    assert tags["ManagedBy"] == "konductor"
```

#### Kubernetes Deployment Tests

```python
# tests/integration/scenarios/test_kubernetes_deployment.py
def test_kubernetes_namespace_creation(
    test_stack,
    kubernetes_client
):
    """Test Kubernetes namespace deployment."""
    # Deploy stack
    up_result = test_stack.up()

    # Get namespace name from outputs
    namespace = up_result.outputs["namespace"].value

    # Validate namespace
    ns = kubernetes_client.read_namespace(namespace)

    assert ns.metadata.name == namespace
    assert ns.metadata.labels["managed-by"] == "konductor"
    assert ns.status.phase == "Active"

def test_kubernetes_resources(test_stack, kubernetes_client):
    """Test Kubernetes resource deployment."""
    outputs = test_stack.outputs()
    namespace = outputs["namespace"].value

    # Check deployments
    deployments = kubernetes_client.list_namespaced_deployment(
        namespace=namespace
    )

    assert any(
        d.metadata.name == "test-deployment"
        for d in deployments.items
    )

    # Check services
    services = kubernetes_client.list_namespaced_service(
        namespace=namespace
    )

    assert any(
        s.metadata.name == "test-service"
        for s in services.items
    )
```

### Validation Helpers

```python
# tests/integration/validation/aws_validators.py
class AWSValidator:
    def __init__(self, client):
        self.client = client

    def validate_vpc_configuration(self, vpc_id: str) -> bool:
        """Validate VPC configuration."""
        vpc = self.client.describe_vpcs(VpcIds=[vpc_id])

        if not vpc["Vpcs"]:
            return False

        vpc = vpc["Vpcs"][0]
        return (
            vpc["CidrBlock"] == "10.0.0.0/16" and
            vpc["EnableDnsHostnames"] and
            vpc["EnableDnsSupport"]
        )

    def validate_security_groups(self, group_id: str) -> bool:
        """Validate security group rules."""
        sg = self.client.describe_security_groups(
            GroupIds=[group_id]
        )["SecurityGroups"][0]

        ingress_rules = sg["IpPermissions"]

        # Check for no public SSH access
        return not any(
            rule["FromPort"] == 22 and
            any(ip["CidrIp"] == "0.0.0.0/0"
                for ip in rule["IpRanges"])
            for rule in ingress_rules
        )
```

### Running Integration Tests

```bash
# Run all integration tests
poetry run pytest tests/integration/

# Run specific scenario
poetry run pytest tests/integration/scenarios/test_aws_deployment.py

# Run with detailed logging
poetry run pytest tests/integration/ -v --log-cli-level=INFO
```

### Integration Testing Best Practices

1. **Resource Cleanup**
   - Always clean up resources after tests
   - Use fixtures for proper teardown
   - Implement cleanup error handling

2. **Cost Management**
   - Use smallest viable resource sizes
   - Limit test duration
   - Clean up resources promptly
   - Monitor testing costs

3. **Error Handling**
   - Implement proper error handling
   - Log detailed error information
   - Handle cleanup failures gracefully

4. **Validation**
   - Validate all created resources
   - Check resource configurations
   - Verify resource interactions
   - Test failure scenarios
