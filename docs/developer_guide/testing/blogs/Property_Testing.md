# Property Testing Infrastructure Code

## Introduction

Property testing leverages Pulumi's Policy as Code (CrossGuard) capabilities to define and enforce infrastructure invariants. While policy packs traditionally enforce organization-wide rules, we can repurpose this functionality for development-time testing to ensure specific infrastructure properties.

## Example: Testing Kubernetes Cluster Configuration

Let's examine how to implement property tests for Kubernetes cluster deployments. Our example will validate:

1. Kubernetes version requirements
2. Network configuration compliance
3. Resource tagging standards

### Setting Up Property Tests

Create a testing directory structure:

```plaintext
konductor/
├── modules/
│   └── kubernetes/
│       └── cluster/
│           ├── deploy.py
│           └── config.py
└── tests/
    └── property/
        ├── __init__.py
        ├── policies/
        │   ├── kubernetes_policies.py
        │   └── network_policies.py
        └── validators/
            └── resource_validators.py
```

### Writing Property Tests

First, let's define our policy pack:

```python
# tests/property/policies/kubernetes_policies.py
from pulumi_policy import (
    PolicyPack,
    ReportViolation,
    ResourceValidationPolicy,
    ResourceValidationArgs
)

def validate_kubernetes_cluster(args: ResourceValidationArgs):
    """Validate Kubernetes cluster configuration."""
    if args.resource_type == "kubernetes:core/v1:Cluster":
        # Get cluster configuration
        version = args.props.get("version")
        network_config = args.props.get("networkConfig", {})

        # Validate Kubernetes version
        if not version or version < "1.24":
            raise ReportViolation(
                f"Cluster must use Kubernetes 1.24 or higher, found: {version}"
            )

        # Validate network configuration
        if network_config.get("vpcType") == "default":
            raise ReportViolation(
                "Clusters must use dedicated VPCs, not default VPC"
            )

        # Validate required tags
        tags = args.props.get("tags", {})
        required_tags = {"environment", "cost-center", "owner"}
        missing_tags = required_tags - set(tags.keys())
        if missing_tags:
            raise ReportViolation(
                f"Missing required tags: {missing_tags}"
            )

kubernetes_policy = ResourceValidationPolicy(
    name="kubernetes-cluster-standards",
    description="Enforce Kubernetes cluster standards",
    validate=validate_kubernetes_cluster
)
```

### Network Configuration Validation

```python
# tests/property/policies/network_policies.py
def validate_network_config(args: ResourceValidationArgs):
    """Validate network configuration."""
    if args.resource_type == "aws:ec2/vpc:Vpc":
        cidr = args.props.get("cidrBlock")
        if not cidr:
            raise ReportViolation("VPC must have CIDR block defined")

        # Validate CIDR range
        if not cidr.startswith("10."):
            raise ReportViolation(
                "VPC CIDR must use private IP space (10.0.0.0/8)"
            )

        # Validate subnets
        subnets = args.props.get("subnets", [])
        if len(subnets) < 3:
            raise ReportViolation(
                "VPC must have at least 3 subnets for high availability"
            )

network_policy = ResourceValidationPolicy(
    name="network-standards",
    description="Enforce network configuration standards",
    validate=validate_network_config
)
```

### Implementation to Test Against

Here's an example cluster implementation that we'll test:

```python
# modules/kubernetes/cluster/deploy.py
from pulumi_kubernetes import Provider
from pulumi_aws import eks

def create_cluster(
    name: str,
    config: dict,
    opts: ResourceOptions = None
) -> eks.Cluster:
    """Create a Kubernetes cluster."""

    # Create cluster without proper configuration
    return eks.Cluster(
        name,
        version="1.23",            # Violates version requirement
        vpc_config={
            "vpcType": "default"   # Violates network requirement
        },
        tags={
            "environment": "dev"    # Missing required tags
        },
        opts=opts
    )
```

### Running Property Tests

To run the tests:

```bash
pulumi up --policy-pack tests/property

Previewing update (dev):
...

Policy Violations:
    [mandatory]  kubernetes-cluster-standards
    Cluster must use Kubernetes 1.24 or higher, found: 1.23

    [mandatory]  kubernetes-cluster-standards
    Clusters must use dedicated VPCs, not default VPC

    [mandatory]  kubernetes-cluster-standards
    Missing required tags: {'cost-center', 'owner'}
```

### Fixing the Implementation

Let's update our implementation to comply with the policies:

```python
# modules/kubernetes/cluster/deploy.py
from pulumi_kubernetes import Provider
from pulumi_aws import eks

def create_cluster(
    name: str,
    config: dict,
    opts: ResourceOptions = None
) -> eks.Cluster:
    """Create a Kubernetes cluster."""

    # Create dedicated VPC
    vpc = create_vpc(f"{name}-vpc")

    return eks.Cluster(
        name,
        version="1.24",
        vpc_config={
            "vpcType": "dedicated",
            "vpcId": vpc.id,
            "subnetIds": vpc.subnet_ids
        },
        tags={
            "environment": "dev",
            "cost-center": "platform-engineering",
            "owner": "platform-team"
        },
        opts=opts
    )
```

Running the tests again:

```bash
pulumi up --policy-pack tests/property

Previewing update (dev):
...

Policy Packs run:
    Name                Version
    property-tests      (local)

No policy violations found
```

## Best Practices

1. **Test Coverage**
   - Test all critical infrastructure properties
   - Include both positive and negative test cases
   - Validate resource relationships

2. **Policy Organization**
   - Group related policies together
   - Use clear, descriptive policy names
   - Document policy requirements

3. **Performance**
   - Keep validation logic efficient
   - Use appropriate enforcement levels
   - Consider test execution order

4. **Maintenance**
   - Keep policies up to date
   - Review and update requirements regularly
   - Document policy changes

## Key Concepts

- **Property Testing**: Validates infrastructure invariants during deployment
- **Policy Packs**: Collections of related infrastructure policies
- **Validation Rules**: Specific checks against resource properties
- **Enforcement Levels**: Mandatory vs. advisory policy violations

These property tests help ensure infrastructure meets requirements before deployment, catching issues early in the development cycle.
