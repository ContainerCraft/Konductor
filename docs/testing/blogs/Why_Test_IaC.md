# Testing Infrastructure with Konductor

## Introduction

Testing infrastructure code has historically been challenging, often leading teams to rely more on manual verification than automated testing. However, with Konductor's Pulumi-based approach using Python, we can bring robust software testing practices to infrastructure development.

Konductor introduces comprehensive testing capabilities that allow you to:

- Test resources before deployment using familiar Python testing tools
- Validate configurations early in the development cycle
- Enforce organizational standards through policy tests
- Build confidence in infrastructure changes

### Why Test Infrastructure?

Consider these common scenarios that proper testing can prevent:

- Misconfigured security groups exposing sensitive services
- IAM permissions that are too permissive
- Resource configurations that violate compliance requirements
- Unexpected dependencies between infrastructure components

By testing infrastructure code, we shift problem detection left - finding issues during development rather than in production. This leads to:

- Faster development cycles
- More reliable deployments
- Reduced costs from fixing production issues
- Increased confidence in infrastructure changes

## The Testing Pyramid for Infrastructure

The traditional testing pyramid emphasizes unit tests as the foundation, with fewer integration and end-to-end tests. However, modern distributed infrastructure requires a modified approach.

Konductor adopts what we call the "Infrastructure Testing Rocket":

```
    /\      End-to-End Tests
   /  \     (Limited, Complex)
  /    \
 /------\   Integration Tests
/        \  (Targeted, Essential)
------------ Unit Tests
|          | (Fast, Frequent)
|          |
------------ Static Tests
            (Continuous, Automated)
```

This model recognizes that:

1. Static testing through Python type hints and Pulumi's type system provides continuous validation
2. Unit tests and integration tests are equally important for infrastructure
3. End-to-end tests, while valuable, should be limited due to complexity and cost

## Core Testing Concepts

### Static Testing

Konductor leverages Python's type system and Pulumi's strong typing to catch issues before execution:

```python
from typing import TypedDict
from pydantic import BaseModel

class SecurityGroupRule(TypedDict):
    protocol: str
    from_port: int
    to_port: int
    cidr_blocks: list[str]

class VpcConfig(BaseModel):
    name: str
    cidr_block: str
    security_group_rules: list[SecurityGroupRule]
```

This enables:
- Early detection of configuration errors
- IDE support with autocompletion
- Documentation through types
- Automated validation

### Unit Testing

Unit tests in Konductor focus on testing resource configurations before deployment. We use Python's pytest framework with Pulumi's mocking capabilities:

```python
@pytest.fixture
def pulumi_mocks():
    """Configure Pulumi resource mocks."""
    from pulumi.runtime import set_mocks
    from typing import Any

    def mock_resource(args: Any):
        return [f"{args.name}_id", args.inputs]

    set_mocks(pulumi.runtime.Mocks(
        new_resource=mock_resource,
        call=lambda *_: {}
    ))
```

Key aspects of unit testing:
- Fast execution with no actual infrastructure
- Testing configuration validation
- Verifying resource properties
- Checking dependency relationships

### Property Testing

Property testing ensures infrastructure meets organizational standards and compliance requirements:

```python
def validate_security_group_rules(args: ResourceValidationArgs):
    """Ensure security groups don't expose sensitive ports."""
    if args.type == "aws:ec2/securityGroup:SecurityGroup":
        for rule in args.props.get("ingress", []):
            if (rule["fromPort"] == 22 and
                "0.0.0.0/0" in rule["cidrBlocks"]):
                raise ValueError("SSH exposed to internet")
```

Property tests:
- Run as part of deployment validation
- Enforce security and compliance rules
- Check resource relationships
- Validate configurations across stacks

### Integration Testing

Integration tests verify interactions between infrastructure components:

```python
@pytest.mark.integration
async def test_vpc_subnet_connectivity():
    """Test VPC subnet connectivity."""
    stack = await create_test_stack()

    try:
        # Deploy test infrastructure
        result = await stack.up()
        assert result.summary.result == "succeeded"

        # Verify subnet connectivity
        vpc = find_vpc_resource(result)
        subnets = find_subnet_resources(result)
        assert await validate_subnet_routing(vpc, subnets)

    finally:
        await stack.destroy()
```

Integration tests:
- Require actual infrastructure deployment
- Test real provider interactions
- Validate cross-resource behavior
- Cost more time and resources to run

## Konductor's Testing Philosophy

Konductor's approach to testing emphasizes:

### Type Safety First
- Leverage Python's type system
- Use Pydantic models for validation
- Enable early error detection
- Provide clear interfaces

### Configuration Validation
- Validate before deployment
- Test configuration combinations
- Check default values
- Verify overrides

### Resource Abstraction
- Mock provider interactions
- Test resource creation
- Validate resource properties
- Check resource relationships

### Mock Provider Patterns
```python
class TestMocks(pulumi.runtime.Mocks):
    def new_resource(self, args):
        # Return predictable resource IDs and states
        if args.type == "aws:ec2/vpc:Vpc":
            return ["vpc-123", {
                "id": "vpc-123",
                "arn": f"arn:aws:ec2:region:account:vpc/vpc-123",
                "cidr_block": args.inputs["cidrBlock"]
            }]
        return [args.name + "_id", args.inputs]
```

### Test Organization
```plaintext
tests/
  ├── conftest.py           # Shared fixtures
  ├── unit/                 # Unit tests
  │   ├── test_config.py
  │   └── test_resources.py
  ├── property/             # Property tests
  │   └── test_compliance.py
  └── integration/          # Integration tests
      └── test_deployment.py
```

By following these principles, Konductor enables comprehensive testing of infrastructure code that:
- Catches issues early
- Enforces standards
- Builds confidence
- Speeds development


# Practical Testing Patterns

After exploring the fundamentals in Part 1, let's dive into practical patterns and real-world examples of testing infrastructure with Konductor. I remember when I first started testing infrastructure code - it felt like trying to test the weather. But with Konductor's structured approach, we can make infrastructure testing both manageable and reliable.

## Test Implementation

### Setting Up Your Testing Environment

First, let's set up a proper testing environment. Konductor's devcontainer makes this straightforward:

```python
# tests/conftest.py
import pytest
from pulumi import automation as auto
from typing import Dict, Any
from modules.core.types import InitializationConfig

@pytest.fixture
def mock_init_config():
    """Create a test initialization configuration."""
    return InitializationConfig(
        pulumi_config={},
        stack_name="test",
        project_name="test-project",
        default_versions={},
        metadata={"labels": {}, "annotations": {}}
    )

@pytest.fixture
def pulumi_mocks():
    """Configure Pulumi mocks for testing."""
    from pulumi.runtime import set_mocks

    def mock_new_resource(args: auto.MockResourceArgs):
        # Return predictable resource IDs and properties
        outputs = args.inputs
        if args.type == "aws:ec2/securityGroup:SecurityGroup":
            outputs["id"] = f"{args.name}-sg-123"
        return [f"{args.name}_id", outputs]

    set_mocks(auto.MockResourceMonitor(
        new_resource_fn=mock_new_resource,
        call_fn=lambda *_: {}
    ))
```

Let me explain why this setup is important. The `mock_init_config` fixture provides a consistent starting point for our tests, while `pulumi_mocks` lets us test infrastructure code without actual cloud resources. Think of it like a flight simulator for your infrastructure.

### Testing Real Infrastructure Components

Let's look at a practical example testing an AWS VPC configuration:

```python
@pytest.mark.asyncio
async def test_vpc_configuration():
    """Test VPC creation and configuration."""
    config = VpcConfig(
        name="test-vpc",
        cidr_block="10.0.0.0/16",
        subnets=[{
            "az": "us-west-2a",
            "cidr": "10.0.1.0/24"
        }]
    )

    vpc = create_vpc(config, mock_init_config)

    # Verify core VPC properties
    assert vpc.cidr_block == "10.0.0.0/16"
    assert vpc.enable_dns_hostnames == True

    # Check required tags
    assert vpc.tags["managed-by"] == "konductor"
```

This test validates both the basic configuration and our organizational standards. I've found that catching misconfigurations here saves hours of debugging later.

### Security Testing Patterns

Security testing is crucial. Here's how we can test security group configurations:

```python
def test_security_group_rules():
    """Ensure security groups follow security standards."""
    group = create_security_group({
        "name": "web-tier",
        "ingress": [{
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["10.0.0.0/8"]
        }]
    })

    def validate_rules(args):
        urn, ingress = args
        # Check for exposed sensitive ports
        for rule in ingress:
            assert not (
                rule["from_port"] == 22 and
                "0.0.0.0/0" in rule["cidr_blocks"]
            ), "SSH exposed to internet"

    return pulumi.Output.all(
        group.urn, group.ingress
    ).apply(validate_rules)
```

I remember a production incident where an exposed port led to a security breach. Tests like these help prevent such issues.

## Testing Best Practices

### Organizing Your Tests

Structure your tests logically:

```plaintext
tests/
├── unit/
│   ├── test_vpc.py        # VPC-specific tests
│   ├── test_security.py   # Security group tests
│   └── test_subnets.py    # Subnet configuration tests
├── property/
│   ├── test_compliance.py # Compliance validations
│   └── test_security.py   # Security policies
└── integration/
    └── test_network.py    # Network connectivity tests
```

### Writing Maintainable Tests

Here's an example of a well-structured test class:

```python
class TestVpcDeployment:
    """Test suite for VPC deployments."""

    @pytest.fixture
    def vpc_config(self):
        """Provide standard VPC configuration."""
        return VpcConfig(
            name="test-vpc",
            cidr_block="10.0.0.0/16"
        )

    def test_vpc_creation(self, vpc_config):
        """Test basic VPC creation."""
        vpc = create_vpc(vpc_config)
        assert vpc.cidr_block == vpc_config.cidr_block

    def test_vpc_subnets(self, vpc_config):
        """Test subnet configuration."""
        vpc = create_vpc(vpc_config)
        assert len(vpc.subnet_ids) > 0
```

### Testing for Failure Cases

Don't forget to test error conditions:

```python
def test_invalid_vpc_configuration():
    """Test handling of invalid VPC configuration."""
    with pytest.raises(ValueError) as excinfo:
        VpcConfig(
            name="invalid-vpc",
            cidr_block="invalid-cidr"
        )
    assert "invalid CIDR format" in str(excinfo.value)
```

## Advanced Testing Scenarios

### Testing Cross-Stack Dependencies

When resources depend on each other across stacks:

```python
@pytest.mark.asyncio
async def test_vpc_peering():
    """Test VPC peering configuration."""
    stack_a = await create_test_stack("vpc-a")
    stack_b = await create_test_stack("vpc-b")

    try:
        # Deploy both VPCs
        vpc_a = await stack_a.up()
        vpc_b = await stack_b.up()

        # Verify peering connection
        peering = create_vpc_peering(
            vpc_a.outputs["vpc_id"],
            vpc_b.outputs["vpc_id"]
        )

        assert await verify_vpc_connectivity(
            vpc_a, vpc_b, peering
        )
    finally:
        await cleanup_stacks([stack_a, stack_b])
```

### Testing Compliance Requirements

Enforce organizational standards:

```python
def test_resource_tagging():
    """Ensure resources have required tags."""
    def check_tags(args: ResourceValidationArgs):
        required_tags = {
            "environment",
            "owner",
            "cost-center"
        }

        tags = args.props.get("tags", {})
        missing = required_tags - set(tags.keys())

        assert not missing, f"Missing required tags: {missing}"

    policy = ResourceValidationPolicy(
        name="required-tags",
        validate=check_tags
    )
```

## CI/CD Integration

Here's how to integrate tests into your CI pipeline:

```yaml
# .github/workflows/infrastructure.yml
name: Infrastructure Tests

on:
  pull_request:
    paths:
      - 'infrastructure/**'
      - 'modules/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Environment
        uses: containercraft/konductor-action@v1

      - name: Run Tests
        run: |
          poetry run pytest tests/unit/
          poetry run pytest tests/property/
```

## Final Thoughts

Remember, the goal isn't to test everything - it's to test the things that matter. Focus on:

1. Security-critical configurations
2. Compliance requirements
3. Complex resource interactions
4. Common failure points

I've found that a well-tested infrastructure codebase gives teams the confidence to make changes quickly and safely. With Konductor's testing capabilities, we can bring the best practices of software testing to infrastructure development.

Join our community to share your testing experiences:
- Discord: [Konductor Community](https://discord.gg/Jb5jgDCksX)
- GitHub Discussions: [Testing Practices](https://github.com/containercraft/konductor/discussions)

The complete source code for all examples is available in the [Konductor repository](https://github.com/containercraft/konductor) under `examples/testing`.

Remember, good testing isn't about catching every possible issue - it's about having confidence in your infrastructure changes and sleeping better at night knowing your safeguards are in place.
