# AWS Module Developer Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Module Architecture](#module-architecture)
3. [Development Standards](#development-standards)
4. [Implementation Guide](#implementation-guide)
5. [Configuration Management](#configuration-management)
6. [Security and Compliance](#security-and-compliance)
7. [Testing and Validation](#testing-and-validation)
8. [Deployment Workflows](#deployment-workflows)
9. [Advanced Topics](#advanced-topics)
10. [Troubleshooting](#troubleshooting)
11. [Future Development](#future-development)
12. [References](#references)

## Introduction

The AWS module for Konductor provides a comprehensive framework for implementing scalable, secure, and compliant AWS infrastructure using Pulumi and Python. This guide details the development standards, implementation patterns, and best practices for contributing to or extending the AWS module.

### Prerequisites

- Python 3.8+
- Poetry for dependency management
- Pulumi CLI
- AWS CLI configured with appropriate credentials
- Understanding of TypedDict and static type checking

### Module Scope

The AWS module handles:
- AWS Organizations and Control Tower setup
- Landing zone implementation
- IAM management and security controls
- EKS cluster deployment
- Integration with AWS services (OpenTelemetry, etc.)

## Module Architecture

### Directory Structure

```
aws/
├── __init__.py
├── types.py          # TypedDict definitions
├── deploy.py         # Deployment logic
├── config.py         # Configuration management
├── iam/             # IAM management
├── organizations/    # AWS Organizations
├── eks/             # EKS implementation
└── security/        # Security controls
```

### Core Components

```python
from typing import TypedDict, Optional, List, Dict

class LandingZone(TypedDict):
    """Landing zone configuration.

    Attributes:
        name: Landing zone name
        email: Account email
        ou_path: Organizational unit path
        tags: Resource tags
    """
    name: str
    email: str
    ou_path: str
    tags: Dict[str, str]

class AWSOrganizationConfig(TypedDict):
    """AWS Organization configuration.

    Attributes:
        enabled: Whether the organization is enabled
        feature_set: Organization feature set
        accounts: List of landing zones
        default_tags: Default resource tags
        region: AWS region
    """
    enabled: bool
    feature_set: str
    accounts: List[LandingZone]
    default_tags: Dict[str, str]
    region: str
```

## Development Standards

### Code Quality Requirements

1. **Type Safety**
   - Use TypedDict for configurations
   - Enable strict type checking with Pyright
   - Implement proper type annotations

2. **Documentation**
   - Comprehensive docstrings
   - Clear inline comments
   - Up-to-date README files

3. **Testing**
   - Unit tests for all functionality
   - Integration tests for workflows
   - Compliance validation tests

### Example Implementation

```python
from typing import Optional, Dict, Any
import pulumi
import pulumi_aws as aws

def create_compliant_resource(
    name: str,
    config: Dict[str, Any],
    compliance_tags: Optional[Dict[str, str]] = None
) -> pulumi.Resource:
    """Create a resource with compliance controls.

    Args:
        name: Resource name
        config: Resource configuration
        compliance_tags: Compliance-related tags

    Returns:
        pulumi.Resource: Created resource with compliance controls
    """
    if not compliance_tags:
        compliance_tags = {}

    # Add required compliance tags
    compliance_tags.update({
        "compliance:framework": "nist",
        "compliance:control": "AC-2",
        "compliance:validated": "true"
    })

    # Create resource with compliance controls
    resource = pulumi.Resource(
        name,
        props={**config, "tags": compliance_tags},
        opts=pulumi.ResourceOptions(protect=True)
    )

    return resource
```

## Implementation Guide

### AWS Organizations Setup

```python
def create_organization(
    config: AWSOrganizationConfig
) -> aws.organizations.Organization:
    """Creates an AWS Organization with all features enabled.

    Args:
        config: Organization configuration

    Returns:
        aws.organizations.Organization: Created organization
    """
    organization = aws.organizations.Organization(
        "aws_organization",
        feature_set=config.get("feature_set", "ALL"),
        opts=pulumi.ResourceOptions(protect=True)
    )
    return organization
```

### Landing Zone Implementation

```python
def create_landing_zone(
    config: LandingZone,
    org_id: str
) -> aws.organizations.Account:
    """Creates a landing zone account.

    Args:
        config: Landing zone configuration
        org_id: Organization ID

    Returns:
        aws.organizations.Account: Created account
    """
    account = aws.organizations.Account(
        f"account-{config['name']}",
        email=config["email"],
        parent_id=org_id,
        tags=config["tags"],
        opts=pulumi.ResourceOptions(protect=True)
    )
    return account
```

## Configuration Management

### TypedDict Configuration

```python
# Default configuration values
aws_organization_defaults: AWSOrganizationConfig = {
    "enabled": True,
    "feature_set": "ALL",
    "accounts": [],
    "default_tags": {},
    "region": "us-west-2"
}
```

### Configuration Validation

```python
def validate_config(config: AWSOrganizationConfig) -> None:
    """Validates AWS configuration.

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if not config["region"]:
        raise ValueError("AWS region must be specified")

    for account in config["accounts"]:
        if not account["email"]:
            raise ValueError("Account email is required")
```

## Security and Compliance

### NIST Controls Implementation

The AWS module implements the following NIST controls:

- AC-2: Account Management
- AC-3: Access Enforcement
- AU-2: Audit Events
- CM-6: Configuration Settings

### Security Best Practices

1. **Organizations Security**
   - Enable AWS Organizations SCP
   - Implement least privilege access
   - Enable CloudTrail logging

2. **Resource Protection**
   - Enable encryption at rest
   - Implement backup policies
   - Configure AWS Config rules

### Example Security Implementation

```python
def configure_security_controls(
    account: aws.organizations.Account
) -> None:
    """Configure security controls for an account.

    Args:
        account: AWS account to configure
    """
    # Enable CloudTrail
    trail = aws.cloudtrail.Trail(
        "audit-trail",
        is_multi_region_trail=True,
        include_global_service_events=True,
        enable_logging=True,
        opts=pulumi.ResourceOptions(parent=account)
    )

    # Configure AWS Config
    aws_config = aws.config.Configuration(
        "aws-config",
        recording_group={
            "all_supported": True,
            "include_global_resources": True
        },
        opts=pulumi.ResourceOptions(parent=account)
    )
```

## Testing and Validation

### Unit Testing

```python
import pytest
from pulumi import automation as auto

def test_organization_creation():
    """Test AWS Organization creation."""
    stack = auto.create_stack(...)
    result = stack.up()

    assert "organization_id" in result.outputs
    assert result.outputs["organization_id"].value != ""
```

### Integration Testing

```python
def test_landing_zone_deployment(
    pulumi_stack: auto.Stack
):
    """Test landing zone deployment workflow."""
    result = pulumi_stack.up()

    assert "account_id" in result.outputs
    assert "ou_id" in result.outputs
```

## Deployment Workflows

### CI/CD Integration

```yaml
name: AWS Module Deployment
on: [push, pull_request]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install Dependencies
        run: |
          pip install poetry
          poetry install
      - name: Deploy Infrastructure
        run: pulumi up --yes
```

## Advanced Topics

### Cross-Account Access Patterns

```python
def setup_cross_account_access(
    source_account: str,
    target_account: str,
    role_name: str
) -> aws.iam.Role:
    """Set up cross-account access role.

    Args:
        source_account: Source AWS account ID
        target_account: Target AWS account ID
        role_name: Name of the role to create

    Returns:
        aws.iam.Role: Created IAM role
    """
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": f"arn:aws:iam::{source_account}:root"
            },
            "Action": "sts:AssumeRole"
        }]
    }

    return aws.iam.Role(
        role_name,
        assume_role_policy=assume_role_policy,
        opts=pulumi.ResourceOptions(
            provider=aws.Provider(f"provider-{target_account}")
        )
    )
```

## Troubleshooting

### Common Issues

1. **Organizations Access Denied**
   - Ensure proper IAM permissions
   - Verify Organization access
   - Check SCP configurations

2. **Landing Zone Deployment Failures**
   - Validate email uniqueness
   - Check OU path existence
   - Verify quota limits

### Best Practices

1. **Resource Management**
   - Use consistent naming conventions
   - Implement proper tagging
   - Enable detailed monitoring

2. **Error Handling**
   - Implement proper error handling
   - Provide meaningful error messages
   - Log deployment failures

## Future Development

### Planned Enhancements

- Complete AWS Organizations integration
- Implement Control Tower automation
- Deploy baseline security controls
- Enhance EKS integration
- Implement cross-account access patterns
- Add advanced monitoring capabilities
- Implement advanced compliance controls
- Add support for AWS Landing Zone

### Long-term Roadmap

1. **Infrastructure Optimization**
   - Multi-region support
   - Disaster recovery automation
   - Advanced cost optimization

2. **Security Enhancements**
   - Zero-trust architecture
   - Advanced threat detection
   - Automated incident response

## References

- [AWS Organizations Documentation](https://docs.aws.amazon.com/organizations/)
- [AWS Control Tower](https://docs.aws.amazon.com/controltower/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [NIST Compliance](https://aws.amazon.com/compliance/nist/)
- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)

---

**Note**: This guide is actively maintained and updated. For the latest changes, refer to the [changelog](./changelog.md) and [implementation roadmap](./implementation_roadmap.md).
