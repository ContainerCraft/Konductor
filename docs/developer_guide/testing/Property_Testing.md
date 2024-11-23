## Property Testing

### Overview

Property testing in Konductor uses Pulumi's CrossGuard capabilities to validate infrastructure properties and enforce compliance rules during deployment. These tests run as part of the deployment process and can validate both resource inputs and outputs.

### Setting Up Property Tests

#### Directory Structure

```plaintext
konductor/
├── tests/
│   ├── property/
│   │   ├── __init__.py
│   │   ├── policies/
│   │   │   ├── aws_policies.py
│   │   │   ├── kubernetes_policies.py
│   │   │   └── security_policies.py
│   │   ├── validators/
│   │   │   ├── resource_validators.py
│   │   │   └── compliance_validators.py
│   │   └── test_properties.py
```

#### Basic Setup

```python
# tests/property/policies/aws_policies.py
from pulumi_policy import (
    PolicyPack,
    ReportViolation,
    ResourceValidationPolicy,
    ResourceValidationArgs
)

def ec2_instance_has_tags(args: ResourceValidationArgs):
    """Ensure EC2 instances have required tags."""
    if args.resource_type == "aws:ec2/instance:Instance":
        tags = args.props.get("tags")
        if not tags:
            raise ReportViolation(
                "EC2 instances must have tags"
            )
        required_tags = {"Environment", "Owner", "CostCenter"}
        missing_tags = required_tags - set(tags.keys())
        if missing_tags:
            raise ReportViolation(
                f"Missing required tags: {missing_tags}"
            )

aws_policies = ResourceValidationPolicy(
    name="aws-required-tags",
    description="Enforce tagging standards for AWS resources.",
    validate=ec2_instance_has_tags
)
```

### Writing Property Tests

#### Resource Properties

```python
# tests/property/validators/resource_validators.py
from pulumi_policy import (
    EnforcementLevel,
    PolicyPack,
    ResourceValidationPolicy
)

def kubernetes_namespace_validation(args: ResourceValidationArgs):
    """Validate Kubernetes namespace configuration."""
    if args.resource_type == "kubernetes:core/v1:Namespace":
        # Check for required labels
        metadata = args.props.get("metadata", {})
        labels = metadata.get("labels", {})

        required_labels = {
            "environment",
            "managed-by",
            "cost-center"
        }

        missing_labels = required_labels - set(labels.keys())
        if missing_labels:
            raise ReportViolation(
                f"Missing required labels: {missing_labels}"
            )

        # Validate namespace naming convention
        name = metadata.get("name", "")
        if not name.startswith(("dev-", "prod-", "stage-")):
            raise ReportViolation(
                "Namespace must start with environment prefix (dev-|prod-|stage-)"
            )

namespace_policy = ResourceValidationPolicy(
    name="namespace-standards",
    description="Enforce namespace standards and conventions",
    validate=kubernetes_namespace_validation
)
```

#### Security Rules

```python
# tests/property/policies/security_policies.py
def validate_security_group_rules(args: ResourceValidationArgs):
    """Validate AWS security group rules."""
    if args.resource_type == "aws:ec2/securityGroup:SecurityGroup":
        ingress_rules = args.props.get("ingress", [])

        for rule in ingress_rules:
            # Check for exposed sensitive ports
            if rule.get("fromPort") in [22, 3389]:
                cidr_blocks = rule.get("cidrBlocks", [])
                if "0.0.0.0/0" in cidr_blocks:
                    raise ReportViolation(
                        f"Port {rule['fromPort']} must not be exposed to the internet"
                    )

            # Validate CIDR blocks
            for cidr in rule.get("cidrBlocks", []):
                if cidr == "0.0.0.0/0" and rule.get("fromPort") != 80:
                    raise ReportViolation(
                        "Open CIDR blocks only allowed for HTTP traffic"
                    )

security_group_policy = ResourceValidationPolicy(
    name="security-group-rules",
    description="Enforce security group best practices",
    validate=validate_security_group_rules
)
```

#### Compliance Rules

```python
# tests/property/validators/compliance_validators.py
def validate_encryption(args: ResourceValidationArgs):
    """Validate resource encryption settings."""
    if args.resource_type == "aws:s3/bucket:Bucket":
        encryption = args.props.get("serverSideEncryptionConfiguration")
        if not encryption:
            raise ReportViolation(
                "S3 buckets must have encryption enabled"
            )

def validate_backup_retention(args: ResourceValidationArgs):
    """Validate backup retention policies."""
    if args.resource_type == "aws:rds/instance:Instance":
        retention = args.props.get("backupRetentionPeriod")
        if not retention or retention < 7:
            raise ReportViolation(
                "RDS instances must retain backups for at least 7 days"
            )

compliance_policies = [
    ResourceValidationPolicy(
        name="encryption-requirements",
        description="Enforce encryption standards",
        validate=validate_encryption
    ),
    ResourceValidationPolicy(
        name="backup-requirements",
        description="Enforce backup retention policies",
        validate=validate_backup_retention
    )
]
```

### Implementing Policy Packs

```python
# tests/property/policies/__init__.py
from pulumi_policy import PolicyPack

from .aws_policies import aws_policies
from .kubernetes_policies import kubernetes_policies
from .security_policies import security_group_policy

konductor_policy_pack = PolicyPack(
    name="konductor-policies",
    enforcement_level="mandatory",
    policies=[
        aws_policies,
        kubernetes_policies,
        security_group_policy,
        *compliance_policies
    ]
)
```

### Running Property Tests

```python
# tests/property/test_properties.py
import pytest
from pulumi import automation as auto
from pulumi_policy import PolicyPackRunner

def test_stack_policies():
    """Test stack against policy pack."""
    # Create stack reference
    stack = auto.create_or_select_stack(
        stack_name="dev",
        project_name="konductor-test",
        program=lambda: None
    )

    # Initialize policy pack runner
    runner = PolicyPackRunner(
        policy_pack=konductor_policy_pack,
        project="konductor-test",
        stack="dev"
    )

    # Run policy evaluation
    result = runner.run()

    # Check for violations
    assert not result.violations, (
        f"Policy violations found: {result.violations}"
    )
```
