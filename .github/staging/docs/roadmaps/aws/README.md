# AWS Module Developer Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Module Overview](#module-overview)
3. [Architecture](#architecture)
4. [Implementation Guide](#implementation-guide)
5. [Configuration Management](#configuration-management)
6. [Development Standards](#development-standards)
7. [Testing and Validation](#testing-and-validation)
8. [Security and Compliance](#security-and-compliance)
9. [Deployment Workflows](#deployment-workflows)
10. [Roadmap and Future Plans](#roadmap-and-future-plans)
11. [Troubleshooting](#troubleshooting)
12. [References](#references)

## Introduction

The AWS module for Konductor provides a comprehensive framework for implementing scalable, secure, and compliant AWS infrastructure using Pulumi and Python. This guide is intended for developers contributing to or extending the AWS module functionality.

### Prerequisites

- Python 3.10+
- Poetry for dependency management
- Pulumi CLI
- AWS CLI configured with appropriate credentials
- Understanding of TypedDict and static type checking

## Module Overview

### Purpose

The AWS module enables:
- Automated AWS Organizations and Control Tower setup
- Standardized landing zone implementation
- Secure IAM management
- EKS cluster deployment with best practices
- Integration with AWS services (OpenTelemetry, etc.)

### Key Features

- Multi-account strategy support
- Compliance-ready infrastructure
- Automated security controls
- Scalable resource management
- Type-safe configuration handling

## Architecture

### Core Components

```python
from typing import TypedDict, Optional, List

class LandingZone(TypedDict):
    name: str
    email: str
    ou_path: str
    tags: Dict[str, str]

class AWSOrganizationConfig(TypedDict):
    enabled: bool
    feature_set: str
    accounts: List[LandingZone]
    default_tags: Dict[str, str]
    region: str
```

### Directory Structure

```
./modules/aws/
├── __init__.py
├── types.py          # TypedDict definitions
├── deploy.py         # Deployment logic
├── config.py         # Configuration management
├── iam/             # IAM management
├── organizations/    # AWS Organizations
├── eks/             # EKS implementation
└── security/        # Security controls
```

## Implementation Guide

### Setting Up AWS Organizations

```python
def create_organization(config: AWSOrganizationConfig) -> aws.organizations.Organization:
    """Creates an AWS Organization with all features enabled."""
    organization = aws.organizations.Organization(
        "aws_organization",
        feature_set=config.get("feature_set", "ALL"),
        opts=pulumi.ResourceOptions(protect=True)
    )
    return organization
```

### Creating Organizational Units

```python
def create_organizational_units(
    organization: aws.organizations.Organization,
    ou_names: List[str]
) -> Dict[str, aws.organizations.OrganizationalUnit]:
    """Creates Organizational Units (OUs) under the AWS Organization."""
    organizational_units = {}
    for ou_name in ou_names:
        ou = aws.organizations.OrganizationalUnit(
            f"ou_{ou_name.lower()}",
            name=ou_name,
            parent_id=organization.roots[0].id,
            opts=pulumi.ResourceOptions(parent=organization)
        )
        organizational_units[ou_name] = ou
    return organizational_units
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
    """Validates AWS configuration."""
    if not config["region"]:
        raise ValueError("AWS region must be specified")

    for account in config["accounts"]:
        if not account["email"]:
            raise ValueError("Account email is required")
```

## Development Standards

### Code Quality Requirements

- Static type checking with Pyright
- Documentation for all public APIs
- Unit tests for new functionality
- Compliance with `PULUMI_PYTHON.md` standards

### Example Implementation

```python
from typing import Optional, Dict, Any
import pulumi

def create_compliant_resource(
    name: str,
    config: Dict[str, Any],
    compliance_tags: Optional[Dict[str, str]] = None
) -> pulumi.Resource:
    """Create a resource with compliance controls."""
    if not compliance_tags:
        compliance_tags = {}

    compliance_tags.update({
        "compliance:framework": "nist",
        "compliance:control": "AC-2",
        "compliance:validated": "true"
    })

    return pulumi.Resource(
        name,
        props={**config, "tags": compliance_tags},
        opts=pulumi.ResourceOptions(protect=True)
    )
```

## Testing and Validation

### Unit Testing

```python
import pytest
from pulumi import automation as auto

def test_vpc_creation():
    """Test VPC creation with default configuration."""
    stack = auto.create_stack(...)
    result = stack.up()
    assert "vpc_id" in result.outputs
```

### Integration Testing

```python
def test_aws_module_integration(pulumi_stack: auto.Stack):
    """Test AWS module integration with core components."""
    result = pulumi_stack.up()
    assert "vpc_id" in result.outputs
    assert "subnet_ids" in result.outputs
```

## Security and Compliance

### NIST Controls Implementation

- AC-2: Account Management
- AC-3: Access Enforcement
- AU-2: Audit Events
- CM-6: Configuration Settings

### Security Best Practices

- Enable AWS Organizations SCP
- Implement least privilege access
- Enable CloudTrail logging
- Configure AWS Config rules

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
      - name: Deploy Infrastructure
        run: pulumi up --yes
```

## Roadmap and Future Plans

- Complete AWS Organizations integration
- Implement Control Tower automation
- Deploy baseline security controls
- Enhance EKS integration
- Implement cross-account access patterns
- Add advanced monitoring capabilities
- Implement advanced compliance controls
- Add support for AWS Landing Zone
- Enhance security posture
- Multi-region support
- Disaster recovery automation
- Advanced cost optimization

## Troubleshooting

### Common Issues

1. **Organizations Access Denied**
   - Ensure proper IAM permissions
   - Verify Organization access

2. **EKS Deployment Failures**
   - Check VPC configuration
   - Verify IAM roles
   - Review security group settings

### Best Practices

1. **Resource Management**
   - Use consistent naming conventions
   - Implement proper tagging
   - Enable detailed monitoring

2. **Security**
   - Regular security assessments
   - Automated compliance checks
   - Continuous monitoring

## References

- [AWS Organizations Documentation](https://docs.aws.amazon.com/organizations/)
- [AWS Control Tower](https://docs.aws.amazon.com/controltower/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [NIST Compliance](https://aws.amazon.com/compliance/nist/)
- [Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/)

---

**Note**: This module is under active development. For the latest updates, refer to the [changelog](./changelog.md) and [implementation roadmap](./implementation_roadmap.md).
