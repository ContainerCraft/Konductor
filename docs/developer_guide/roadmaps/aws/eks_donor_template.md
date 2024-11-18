# Amazon EKS Cluster Template Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Implementation Guide](#implementation-guide)
5. [Configuration Management](#configuration-management)
6. [Security Controls](#security-controls)
7. [Observability Integration](#observability-integration)
8. [Deployment Workflow](#deployment-workflow)
9. [Testing and Validation](#testing-and-validation)
10. [Best Practices](#best-practices)
11. [Future Enhancements](#future-enhancements)
12. [Troubleshooting](#troubleshooting)
13. [References](#references)

## Introduction

This guide provides a comprehensive template for deploying production-ready Amazon EKS clusters using Pulumi and Python. It implements AWS best practices, security controls, and observability patterns while maintaining compliance with organizational standards.

### Purpose

- Provide a standardized EKS deployment template
- Implement security best practices
- Enable comprehensive observability
- Ensure compliance with standards
- Support multi-tenant workloads

### Scope

- EKS cluster deployment
- VPC and networking setup
- IAM and security configuration
- Logging and monitoring
- Add-on integration (ADOT, Fluent Bit)

## Architecture Overview

### Core Components

```python
from typing import TypedDict, Optional, List

class EksClusterConfig(TypedDict):
    """EKS cluster configuration structure.

    Attributes:
        name: Cluster name
        version: Kubernetes version
        vpc_config: VPC configuration
        node_groups: Node group configurations
        addons: Cluster add-ons
    """
    name: str
    version: str
    vpc_config: Dict[str, Any]
    node_groups: List[Dict[str, Any]]
    addons: Optional[Dict[str, Any]]
```

### Network Architecture

- VPC with public and private subnets
- NAT Gateways for outbound traffic
- VPC Flow Logs for network monitoring
- Security group configuration

### Security Architecture

- Private API endpoint
- KMS encryption for secrets
- IAM roles and policies
- Network policies

## Prerequisites

- Python 3.10+
- Pulumi CLI
- AWS CLI configured
- Required permissions:
  - EKS cluster creation
  - VPC management
  - IAM role creation
  - KMS key management

## Implementation Guide

### VPC Setup

```python
def create_vpc(
    stack_name: str,
    cidr_block: str,
    azs: List[str]
) -> aws_native.ec2.VPC:
    """Create VPC with required components."""
    vpc = aws_native.ec2.VPC(
        f"vpc-{stack_name}",
        cidr_block=cidr_block,
        enable_dns_support=True,
        enable_dns_hostnames=True,
        tags=[aws_native.ec2.TagArgs(
            key="Name",
            value=f"vpc-{stack_name}"
        )]
    )
    return vpc
```

### Security Group Configuration

```python
def create_security_groups(
    stack_name: str,
    vpc_id: pulumi.Output[str]
) -> Dict[str, aws_native.ec2.SecurityGroup]:
    """Create required security groups."""
    cluster_sg = aws_native.ec2.SecurityGroup(
        f"cluster-sg-{stack_name}",
        vpc_id=vpc_id,
        description="EKS cluster security group",
        tags=[aws_native.ec2.TagArgs(
            key="Name",
            value=f"cluster-sg-{stack_name}"
        )]
    )
    return {"cluster": cluster_sg}
```

### EKS Cluster Deployment

```python
def create_eks_cluster(
    config: EksClusterConfig,
    vpc_id: pulumi.Output[str],
    subnet_ids: List[pulumi.Output[str]],
    security_groups: Dict[str, aws_native.ec2.SecurityGroup]
) -> aws_native.eks.Cluster:
    """Create EKS cluster with configuration."""
    cluster = aws_native.eks.Cluster(
        config["name"],
        role_arn=config["role_arn"],
        version=config["version"],
        vpc_config=aws_native.eks.ClusterVpcConfigArgs(
            subnet_ids=subnet_ids,
            security_group_ids=[security_groups["cluster"].id],
            endpoint_private_access=True,
            endpoint_public_access=False
        ),
        encryption_config=[
            aws_native.eks.ClusterEncryptionConfigArgs(
                provider=aws_native.eks.ProviderArgs(
                    key_arn=config["kms_key_arn"]
                ),
                resources=["secrets"]
            )
        ]
    )
    return cluster
```

## Configuration Management

### TypedDict Configurations

```python
class NodeGroupConfig(TypedDict):
    name: str
    instance_types: List[str]
    desired_size: int
    min_size: int
    max_size: int
    disk_size: int
    labels: Dict[str, str]
    taints: Optional[List[Dict[str, str]]]

class VpcConfig(TypedDict):
    cidr_block: str
    public_subnet_cidrs: List[str]
    private_subnet_cidrs: List[str]
    availability_zones: List[str]
```

### Default Values

```python
eks_defaults: EksClusterConfig = {
    "version": "1.26",
    "vpc_config": {
        "cidr_block": "10.0.0.0/16",
        "public_subnet_cidrs": [
            "10.0.0.0/24",
            "10.0.1.0/24"
        ],
        "private_subnet_cidrs": [
            "10.0.2.0/24",
            "10.0.3.0/24"
        ]
    },
    "node_groups": [{
        "name": "default",
        "instance_types": ["t3.medium"],
        "desired_size": 2,
        "min_size": 1,
        "max_size": 4
    }]
}
```

## Security Controls

### IAM Configuration

```python
def create_cluster_role(
    stack_name: str
) -> aws_native.iam.Role:
    """Create IAM role for EKS cluster."""
    return aws_native.iam.Role(
        f"eks-cluster-role-{stack_name}",
        assume_role_policy_document=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "eks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        })
    )
```

### KMS Configuration

```python
def create_kms_key(
    stack_name: str
) -> aws_native.kms.Key:
    """Create KMS key for EKS secrets encryption."""
    return aws_native.kms.Key(
        f"eks-kms-key-{stack_name}",
        description="KMS key for EKS secrets encryption",
        enable_key_rotation=True
    )
```

## Observability Integration

### Fluent Bit Setup

```python
def deploy_fluent_bit(
    provider: k8s.Provider,
    namespace: str = "logging"
) -> None:
    """Deploy Fluent Bit for log collection."""
    # Implementation details in the full code example
```

### ADOT Integration

```python
def deploy_adot(
    provider: k8s.Provider,
    namespace: str = "adot-system"
) -> None:
    """Deploy AWS Distro for OpenTelemetry."""
    # Implementation details in the full code example
```

## Deployment Workflow

1. Create VPC and networking components
2. Set up security groups and IAM roles
3. Deploy EKS cluster
4. Configure node groups
5. Install cluster add-ons
6. Deploy observability components

## Testing and Validation

### Health Checks

```python
def validate_cluster_health(
    cluster_name: str
) -> bool:
    """Validate EKS cluster health."""
    try:
        cluster = aws.eks.get_cluster(name=cluster_name)
        return cluster.status == "ACTIVE"
    except Exception as e:
        log.error(f"Cluster validation failed: {str(e)}")
        return False
```

### Integration Tests

```python
def test_cluster_deployment(
    stack: auto.Stack
) -> None:
    """Test full cluster deployment."""
    # Implementation details
```

## Best Practices

1. **Security**
   - Enable private endpoints
   - Implement least privilege
   - Use KMS encryption
   - Enable audit logging

2. **Networking**
   - Use private subnets for nodes
   - Implement proper CIDR planning
   - Enable VPC Flow Logs

3. **Observability**
   - Deploy ADOT collector
   - Configure Fluent Bit
   - Enable CloudWatch Container Insights

## Future Enhancements

### Short-term

1. **Advanced Networking**
   - VPC CNI customization
   - Network policy implementation
   - Service mesh integration

2. **Security Enhancements**
   - Pod security policies
   - Runtime security
   - Image scanning

### Long-term

1. **Multi-cluster Management**
   - Cluster federation
   - Cross-cluster networking
   - Centralized operations

2. **Advanced Observability**
   - Custom metrics pipeline
   - Automated alerting
   - Performance optimization

## Troubleshooting

### Common Issues

1. **Cluster Creation Failures**
   - Check IAM permissions
   - Verify VPC configuration
   - Review security group rules

2. **Node Group Issues**
   - Validate instance types
   - Check capacity constraints
   - Review launch template

### Logging and Debugging

```python
def configure_debug_logging(
    level: str = "DEBUG"
) -> None:
    """Configure debug logging for troubleshooting."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
```

## References

- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Pulumi AWS Native Provider](https://www.pulumi.com/registry/packages/aws-native/)
- [ADOT Documentation](https://aws-otel.github.io/)
- [Fluent Bit Documentation](https://docs.fluentbit.io/)

---

**Note**: This template is actively maintained and updated. For the latest changes, refer to the [changelog](./changelog.md).
