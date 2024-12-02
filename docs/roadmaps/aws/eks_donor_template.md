# Amazon EKS cluster template guide

## Table of Contents

1. [Introduction](#introduction)
   - [Purpose](#purpose)
   - [Scope](#scope)
2. [Architecture overview](#architecture-overview)
   - [Core components](#core-components)
3. [Prerequisites](#prerequisites)
4. [Implementation guide](#implementation-guide)
   - [Project setup](#project-setup)
   - [Configuration setup](#configuration-setup)
   - [Deployment steps](#deployment-steps)
5. [Configuration management](#configuration-management)
6. [Security controls](#security-controls)
   - [IAM roles and policies](#iam-roles-and-policies)
   - [Network security](#network-security)
7. [Observability integration](#observability-integration)
   - [ADOT integration](#adot-integration)
   - [Fluent Bit logging](#fluent-bit-logging)
8. [Deployment workflow](#deployment-workflow)
9. [Testing and validation](#testing-and-validation)
   - [Unit tests](#unit-tests)
   - [Integration tests](#integration-tests)
10. [Best practices](#best-practices)
11. [Future enhancements](#future-enhancements)
12. [Troubleshooting](#troubleshooting)
    - [Common issues](#common-issues)
    - [Logging and debugging](#logging-and-debugging)
13. [Conclusion](#conclusion)
14. [References](#references)

---

## Introduction

This guide provides a comprehensive template for deploying production-ready Amazon Elastic Kubernetes Service (EKS) clusters using Pulumi and Python. It implements AWS best practices, security controls, and observability patterns while maintaining compliance with organizational standards.

### Purpose

- Provide a standardized EKS deployment template.
- Implement security best practices.
- Enable comprehensive observability.
- Ensure compliance with standards.
- Support multi-tenant workloads.

### Scope

- EKS cluster deployment.
- VPC and networking setup.
- IAM and security configuration.
- Logging and monitoring.
- Add-on integration (ADOT, Fluent Bit).

---

## Architecture overview

### Core components

```python
from typing import TypedDict, List, Optional, Dict

class NodeGroupConfig(TypedDict):
    """Node group configuration structure.

    Attributes:
        name: The name of the node group.
        instance_type: The EC2 instance type.
        desired_capacity: The desired number of nodes.
        min_size: The minimum number of nodes.
        max_size: The maximum number of nodes.
        ssh_key_name: The name of the SSH key pair.
        tags: Optional tags for the node group resources.
    """

class EksClusterConfig(TypedDict):
    """EKS cluster configuration structure.

    Attributes:
        name: The name of the EKS cluster.
        version: The Kubernetes version.
        region: The AWS region.
        node_groups: A list of node group configurations.
        tags: Optional tags for the cluster resources.
    """
```

---

## Prerequisites

> **Note**: All prerequisites are automatically supplied via the [Konductor Devcontainer](../../developer_guide/devcontainer.md).

Before proceeding, ensure you have the following:

- **Python 3.10+**: The codebase requires Python version 3.10 or higher.
- **Pulumi CLI**: Install the Pulumi CLI and authenticate with your cloud provider.
- **AWS CLI**: Configure the AWS CLI with appropriate credentials.
- **Poetry**: Use Poetry for dependency management.
- **SSH key pair**: An existing SSH key pair in AWS for EC2 instances.
- **IAM permissions**: Ensure your AWS user has sufficient permissions to create and manage the required resources.

---

## Implementation guide

### Configuration setup

Configure the Pulumi stack with the required variables:

```bash
pulumi stack init dev
pulumi config set aws:region us-west-2
pulumi config set ssh_key_name your-ssh-key
```

### Deployment steps

1. **Preview changes**:

   ```bash
   pulumi preview
   ```

2. **Deploy resources**:

   ```bash
   pulumi up
   ```

3. **Access the cluster**:

   Update your kubeconfig file to access the cluster:

   ```bash
   pulumi stack output kubeconfig > kubeconfig.yaml
   export KUBECONFIG=$PWD/kubeconfig.yaml
   kubectl get nodes
   ```

---

## Configuration management

The EKS module uses `TypedDict` for configuration validation and management. Configurations are defined in the `types.py` file and consumed by the deployment logic. Configuration is merged from multiple sources, including Pulumi configuration files and environment variables, and is validated upon initialization.

---

## Security controls

### IAM roles and policies

For security and compliance, the module creates and configures the necessary IAM roles and policies with least privilege principles.

- **Cluster role**: Attached with policies for EKS cluster operations.
- **Node group role**: Attached with policies for worker node operations.

### Network security

- **VPC and subnets**: The VPC and subnets are created with appropriate CIDR blocks and tags.
- **Security groups**: Security groups are configured to allow only necessary traffic.
- **Endpoint access**: The EKS cluster endpoint access is restricted as per compliance requirements.

---

## Observability integration

### ADOT integration

Configure AWS Distro for OpenTelemetry (ADOT) collectors to export metrics and traces to AWS CloudWatch and X-Ray.

```python
def deploy_adot_integration(cluster: EksCluster) -> None:
    """Deploy ADOT OpenTelemetry collectors to the EKS cluster.

    Args:
        cluster: The EKS cluster object.
    """
    # Implementation of ADOT deployment
```

### Fluent Bit logging

Set up Fluent Bit as a DaemonSet to collect and forward logs to AWS CloudWatch Logs.

---

## Deployment workflow

The deployment workflow follows best practices for infrastructure provisioning:

1. **Initialize Pulumi stack**.
2. **Set configuration values**.
3. **Preview changes** before applying.
4. **Deploy resources** using `pulumi up`.
5. **Validate** the deployment and access the cluster.

---

## Testing and validation

### Unit tests

Implement unit tests using `pytest` to ensure configuration validation and resource creation.

```python
def test_eks_cluster_creation() -> None:
    """Test EKS cluster creation."""
    # Test implementation
```

### Integration tests

Use Pulumi's testing framework for integration tests to validate resource provisioning and configurations.

---

## Best practices

- **Type safety**: Use type hints and enforce strict typing throughout the codebase.
- **Modular design**: Separate configurations, types, and resource definitions into distinct modules.
- **Security**: Follow AWS security best practices, including least privilege IAM policies.
- **Compliance**: Ensure all resources adhere to compliance standards such as NIST and FISMA.
- **Observability**: Implement comprehensive logging and monitoring from the start.

---

## Future enhancements

- **Automated scaling**: Implement Cluster Autoscaler and Horizontal Pod Autoscaler.
- **Advanced networking**: Integrate with AWS Transit Gateway and implement network policies.
- **Enhanced security**: Add OPA Gatekeeper and enable encryption at rest for etcd.
- **Multi-cluster management**: Explore Kubernetes federation and multi-cluster management tools.

---

## Troubleshooting

### Common issues

1. **Cluster creation failures**:

   - Verify IAM permissions.
   - Check VPC and subnet configurations.
   - Ensure that the SSH key pair exists.

2. **Node group scaling issues**:

   - Check instance type availability.
   - Validate Auto Scaling Group settings.

### Logging and debugging

Enable debug logging in Pulumi and AWS SDKs to gather more information:

```python
import logging

def configure_debug_logging(level: str = "DEBUG") -> None:
    """Configure debug logging for troubleshooting.

    Args:
        level: The logging level to set.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
```

---

## Conclusion

By following this guide, you can deploy a production-ready Amazon EKS cluster that adheres to best practices and compliance requirements. The template provides a solid foundation for building scalable, secure, and observable Kubernetes workloads on AWS.

---

## References

- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Pulumi AWS Native Provider](https://www.pulumi.com/registry/packages/aws-native/)
- [ADOT Documentation](https://aws-otel.github.io/)
- [Fluent Bit Documentation](https://docs.fluentbit.io/)
- [Konductor Developer Guide](../../developer_guide/README.md)
- [Pulumi Python Development Guide](../../developer_guide/pulumi-python.md)
- [Documentation Style Guide](../../developer_guide/documentation.md)
- [Contribution Guidelines](../../contribution_guidelines.md)

---

*Note*: This template is actively maintained and updated. Refer to the [changelog](./changelog.md) for the latest changes.
