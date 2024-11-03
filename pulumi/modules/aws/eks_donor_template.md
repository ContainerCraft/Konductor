# DEVELOPER.md

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Project Overview](#project-overview)
- [Architecture Diagram](#architecture-diagram)
- [Technologies Used](#technologies-used)
- [Key Features and Techniques](#key-features-and-techniques)
- [Code Walkthrough](#code-walkthrough)
  - [Configuration and Imports](#configuration-and-imports)
  - [IAM Roles](#iam-roles)
  - [VPC and Networking](#vpc-and-networking)
  - [Security Groups](#security-groups)
  - [Amazon EKS Cluster and Node Group](#amazon-eks-cluster-and-node-group)
  - [KMS Key for Secrets Encryption](#kms-key-for-secrets-encryption)
  - [VPC Flow Logs](#vpc-flow-logs)
  - [Kubernetes Provider and Kubeconfig](#kubernetes-provider-and-kubeconfig)
  - [Fluent Bit Deployment for Logging](#fluent-bit-deployment-for-logging)
- [Pulumi Configuration](#pulumi-configuration)
- [Type Checking and Poetry](#type-checking-and-poetry)
- [Deployment Instructions](#deployment-instructions)
- [Conclusion](#conclusion)
- [References](#references)

---

## Introduction

This provides a comprehensive explanation of the Pulumi Infrastructure as Code (IaC) eks_donor_template.py iac donor code written in Python. The project sets up a complete Amazon EKS (Elastic Kubernetes Service) cluster with supporting AWS infrastructure, including networking components, IAM roles, security groups, and logging configurations using Fluent Bit.

This guide is intended for developers and DevOps engineers who require a deep understanding of the codebase, the resources created, their interrelationships, and the reasoning behind the code structure and design choices.

---

## Prerequisites

- Familiarity with Python programming language.
- Basic understanding of AWS services like VPC, EKS, IAM, and CloudWatch.
- Knowledge of Kubernetes concepts.
- Installed tools:
  - [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
  - [Poetry](https://python-poetry.org/docs/#installation)
  - AWS CLI configured with appropriate credentials.

---

## Project Overview

The project automates the creation of an AWS EKS cluster using Pulumi's Python SDKs. It leverages modern Python features and Pulumi's latest enhancements to provide a clean, type-safe, and Pythonic codebase.

Key components include:

- **VPC and Networking**: Custom VPC with public and private subnets, NAT Gateway, and routing configurations.
- **IAM Roles**: Roles for EKS cluster and node groups with necessary policies.
- **Security Groups**: For controlling traffic between cluster components.
- **EKS Cluster and Node Group**: Configured with private endpoints and KMS encryption for secrets.
- **Logging**: Deployment of Fluent Bit as a DaemonSet for application logging to CloudWatch.
- **VPC Flow Logs**: Capture network traffic logs for the VPC.
- **Type Checking and Package Management**: Integration with Pyright for type checking and Poetry for dependency management.

---

## Architecture Diagram

```
+-------------------------+
|      AWS Account        |
| +---------------------+ |
| |        VPC          | |
| | +-----------------+ | |
| | |   EKS Cluster   | | |
| | |                 | | |
| | | +-------------+ | | |
| | | | Node Group  | | | |
| | | +-------------+ | | |
| | +-----------------+ | |
| +---------------------+ |
+-------------------------+
```

---

## Technologies Used

- **Pulumi**: Infrastructure as Code platform for managing cloud resources.
- **Python**: Programming language used for scripting and IaC definitions.
- **Poetry**: Python dependency management tool.
- **Pyright**: Static type checker for Python.
- **AWS Native SDK**: Pulumi provider for AWS services using the AWS Cloud Control API.
- **Kubernetes SDK**: Pulumi provider for Kubernetes resources.

---

## Key Features and Techniques

- **Pythonic Input Types**: Utilizes dictionaries with type hints (`TypedDict`) for resource inputs, offering a concise and readable syntax with type safety.
- **Native Support for Poetry**: Manages Python dependencies and virtual environments using Poetry for consistency and ease of use.
- **Type Checking with Pyright**: Integrates Pyright to perform static type checking, ensuring code correctness and reliability.
- **AWS Native Provider**: Uses `pulumi_aws_native` for AWS resource provisioning, aligning closely with AWS CloudFormation.
- **Kubernetes Resource Deployment**: Deploys Kubernetes resources like Namespaces, ConfigMaps, ServiceAccounts, and DaemonSets using Pulumi's Kubernetes SDK.

---

## Code Walkthrough

### Configuration and Imports

```python
import base64
import json
import pulumi
import pulumi_aws as aws
import pulumi_aws_native as aws_native
import pulumi_kubernetes as k8s

# Get the current Pulumi stack name
stack_name = pulumi.get_stack()

# Load configuration values
config = pulumi.Config()
```

- **Imports**: The code imports necessary modules, including Pulumi SDKs for AWS and Kubernetes.
- **Stack Name**: Retrieves the current Pulumi stack name, used for resource naming.
- **Configuration**: Loads configuration values from `Pulumi.<stack_name>.yaml`.

### IAM Roles

#### EKS Cluster Role

```python
eks_role = aws_native.iam.Role(f"eksRole-{stack_name}",
    assume_role_policy_document=json.dumps({
        # Policy document
    }),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
        "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
    ],
    role_name=eks_role_name,
)
```

- **Purpose**: Allows EKS to interact with other AWS services.
- **Assume Role Policy**: Grants EKS service permission to assume this role.
- **Managed Policies**: Attaches necessary policies for cluster operations.

#### Node Group Role

```python
node_role = aws_native.iam.Role(f"nodeRole-{stack_name}",
    assume_role_policy_document=json.dumps({
        # Policy document
    }),
    managed_policy_arns=[
        # Policies for worker nodes
    ],
    role_name=node_role_name,
)
```

- **Purpose**: Allows EC2 instances (worker nodes) to interact with AWS services.
- **Policies**: Provides permissions for nodes to communicate within the cluster and with AWS services.

### VPC and Networking

#### VPC Creation

```python
vpc = aws_native.ec2.VPC(f"vpc-{stack_name}",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": f"vpc-{stack_name}"}
)
```

- **CIDR Block**: Defines the IP range for the VPC.
- **DNS Support**: Enabled for internal DNS resolution.
- **Tags**: Used for identification and management.

#### Subnets

```python
public_subnets = []
private_subnets = []

for i, az in enumerate(azs):
    public_subnet = aws_native.ec2.Subnet(
        # Subnet configuration
    )
    private_subnet = aws_native.ec2.Subnet(
        # Subnet configuration
    )
    public_subnets.append(public_subnet)
    private_subnets.append(private_subnet)
```

- **Public Subnets**: For resources that need internet access.
- **Private Subnets**: For internal resources, like EKS worker nodes.
- **Availability Zones**: Distributes subnets across multiple AZs for redundancy.

#### Internet Gateway and NAT Gateway

- **Internet Gateway (IGW)**: Enables internet access for resources in public subnets.
- **NAT Gateway**: Allows instances in private subnets to access the internet while remaining unreachable from the outside.

#### Route Tables and Associations

- **Route Tables**: Define how traffic is directed within the VPC.
- **Associations**: Link subnets to route tables to apply routing rules.

### Security Groups

```python
cluster_security_group = aws_native.ec2.SecurityGroup(
    # Cluster security group configuration
)

node_security_group = aws_native.ec2.SecurityGroup(
    # Node group security group configuration
)
```

- **Cluster Security Group**: Controls traffic to the EKS control plane.
- **Node Security Group**: Controls traffic to and from worker nodes.
- **Ingress and Egress Rules**: Defined to allow necessary communication between cluster components and to permit SSH access.

### Amazon EKS Cluster and Node Group

#### KMS Key for Secrets Encryption

```python
kms_key = aws_native.kms.Key(f"kmsKey-{stack_name}",
    description="KMS key for EKS secrets encryption",
    enable_key_rotation=True
)
```

- **Purpose**: Encrypts Kubernetes secrets at rest using AWS KMS.

#### EKS Cluster Creation

```python
eks_cluster = aws_native.eks.Cluster(f"eksCluster-{stack_name}",
    name=eks_cluster_name,
    role_arn=eks_role.arn,
    version="1.26",
    encryption_config=[{
        "provider": {"key_arn": kms_key.key_arn},
        "resources": ["secrets"]
    }],
    resources_vpc_config={
        # VPC configuration
    },
    enabled_cluster_log_types=[
        "api", "audit", "authenticator", "controllerManager", "scheduler"
    ],
    tags={"Name": eks_cluster_name}
)
```

- **Version**: Specifies the Kubernetes version.
- **Encryption Config**: Uses the KMS key for encrypting secrets.
- **VPC Config**: Attaches the cluster to private subnets and security groups.
- **Cluster Logging**: Enables logging for critical components.

#### Node Group Creation

```python
node_group = aws_native.eks.Nodegroup(f"nodeGroup-{stack_name}",
    cluster_name=eks_cluster.name,
    node_role=node_role.arn,
    subnets=[subnet.id for subnet in private_subnets],
    nodegroup_name=nodegroup_name,
    scaling_config={
        "desired_size": desired_capacity,
        "min_size": min_size,
        "max_size": max_size,
    },
    instance_types=[instance_type],
    remote_access={
        "ec2_ssh_key": ssh_key_name,
        "source_security_groups": [node_security_group.id],
    },
    tags={"Name": nodegroup_name}
)
```

- **Scaling Config**: Manages the number of worker nodes.
- **Instance Types**: Defines the EC2 instance types for the nodes.
- **Remote Access**: Configures SSH access to nodes using the specified key pair.

### VPC Flow Logs

```python
flow_logs_role = aws_native.iam.Role(f"vpcFlowLogsRole-{stack_name}",
    # Role configuration
)

flow_log_group = aws_native.logs.LogGroup(f"vpcFlowLogGroup-{stack_name}",
    log_group_name=f"/aws/vpc/flowlogs/{vpc.id}",
    retention_in_days=90,
    tags={"Name": f"vpcFlowLogGroup-{stack_name}"}
)

vpc_flow_log = aws_native.ec2.FlowLog(f"vpcFlowLog-{stack_name}",
    resource_id=vpc.id,
    resource_type="VPC",
    traffic_type="ALL",
    log_destination_type="cloud-watch-logs",
    log_group_name=flow_log_group.name,
    deliver_logs_permission_arn=flow_logs_role.arn
)
```

- **Purpose**: Captures detailed information about network traffic in the VPC.
- **Flow Logs Role**: Allows VPC Flow Logs service to write logs to CloudWatch.
- **Log Group**: Stores the flow logs in CloudWatch Logs.

### Kubernetes Provider and Kubeconfig

#### Generate Kubeconfig

```python
def generate_kubeconfig(cluster_name, cluster_endpoint, cluster_certificate_authority):
    kubeconfig = {
        # Kubeconfig structure
    }
    return kubeconfig
```

- **Purpose**: Creates a kubeconfig file for authenticating with the EKS cluster.
- **Components**:
  - **Cluster Info**: Endpoint and certificate data.
  - **User Info**: Uses AWS IAM authentication.

#### Create Kubernetes Provider

```python
k8s_provider = k8s.Provider(f"k8sProvider-{stack_name}",
    kubeconfig=kubeconfig
)
```

- **Purpose**: Allows Pulumi to manage Kubernetes resources within the EKS cluster.
- **Kubeconfig**: Provides authentication and connection details.

### Fluent Bit Deployment for Logging

#### Namespace Creation

```python
fluent_bit_namespace = k8s.core.v1.Namespace("fluent-bit-namespace",
    metadata={"name": "logging"},
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)
```

- **Purpose**: Isolates logging resources in a dedicated namespace.

#### ConfigMap for Fluent Bit

```python
fluent_bit_config_map = k8s.core.v1.ConfigMap("fluent-bit-config",
    metadata={
        "name": "fluent-bit-config",
        "namespace": "logging"
    },
    data={
        "fluent-bit.conf": """
        # Fluent Bit configuration
        """,
        "parsers.conf": """
        # Parser configuration
        """
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)
```

- **Purpose**: Provides configuration files for Fluent Bit.

#### Service Account, Cluster Role, and Binding

```python
fluent_bit_service_account = k8s.core.v1.ServiceAccount("fluent-bit-sa",
    # Service account configuration
)

fluent_bit_cluster_role = k8s.rbac.v1.ClusterRole("fluent-bit-cluster-role",
    # Cluster role configuration
)

fluent_bit_cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding("fluent-bit-cluster-role-binding",
    # Cluster role binding configuration
)
```

- **Purpose**: Grants Fluent Bit permissions to read Kubernetes metadata.

#### DaemonSet Deployment

```python
fluent_bit_daemonset = k8s.apps.v1.DaemonSet("fluent-bit-daemonset",
    metadata={
        "name": "fluent-bit",
        "namespace": "logging",
        "labels": {"k8s-app": "fluent-bit-logging"}
    },
    spec={
        # DaemonSet specification
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider)
)
```

- **Purpose**: Deploys Fluent Bit agents on each node to collect and forward logs.
- **Configuration**: Mounts necessary volumes and uses the provided ConfigMap for settings.

---

## Pulumi Configuration

The `Pulumi.yaml` file has been updated to leverage new features:

```yaml
name: your-project-name
runtime:
  name: python
  options:
    toolchain: poetry
    typechecker: pyright
```

- **Toolchain (Poetry)**: Specifies that Poetry should be used for dependency management.
- **Typechecker (Pyright)**: Integrates Pyright for static type checking during Pulumi operations.

---

## Type Checking and Poetry

### Type Checking with Pyright

- **Integration**: Pyright is specified in `Pulumi.yaml` and will run automatically during Pulumi deployments.
- **Benefits**:
  - Early detection of type errors.
  - Ensures code adheres to expected interfaces and data structures.
- **Usage**: No additional steps required; Pulumi will invoke Pyright as configured.

### Dependency Management with Poetry

- **Initialization**: Run `poetry init` to set up the project.
- **Adding Dependencies**:

  ```bash
  poetry add pulumi pulumi-aws pulumi-aws-native pulumi-kubernetes
  ```

- **Virtual Environment**: Poetry manages a virtual environment, isolating project dependencies.

---

## Deployment Instructions

1. **Install Poetry**: If not already installed, follow the [Poetry installation guide](https://python-poetry.org/docs/#installation).

2. **Initialize the Project**:

   ```bash
   poetry init
   ```

   - Answer the prompts to set up `pyproject.toml`.

3. **Add Dependencies**:

   ```bash
   poetry add pulumi pulumi-aws pulumi-aws-native pulumi-kubernetes
   ```

4. **Configure AWS Credentials**:

   - Ensure that AWS CLI is configured with the necessary credentials and permissions.

5. **Set Required Configurations**:

   ```bash
   pulumi config set aws:region <your-aws-region>
   pulumi config set ssh_key_name <your-ssh-key-name> --secret
   ```

6. **Install Project Dependencies**:

   ```bash
   poetry install
   ```

7. **Deploy the Stack**:

   ```bash
   pulumi up
   ```

   - Pulumi will run Pyright for type checking before deployment.
   - Review the changes and confirm the deployment.

---

## Conclusion

This project demonstrates the use of Pulumi's latest Python features to define and manage AWS infrastructure in a concise, readable, and type-safe manner. By adopting modern Python techniques and tools like Poetry and Pyright, the codebase becomes more maintainable and robust.

Key takeaways:

- **Pythonic Code**: Using dictionaries with type hints enhances readability without sacrificing type safety.
- **Modern Tooling**: Integration with Poetry and Pyright streamlines development and ensures code quality.
- **Feature-Complete IaC**: The project sets up a production-ready EKS cluster with best practices, including security, networking, and logging.

---

## References

- **Pulumi Documentation**:
  - [Python in Pulumi](https://www.pulumi.com/docs/intro/languages/python/)
  - [AWS Native Provider](https://www.pulumi.com/registry/packages/aws-native/)
  - [Kubernetes Provider](https://www.pulumi.com/registry/packages/kubernetes/)
- **Blog Post**:
  - [Pulumi + Python: Bringing the Best of Modern Python to IaC](https://www.pulumi.com/blog/pulumi-loves-python/)
- **Poetry**:
  - [Official Documentation](https://python-poetry.org/docs/)
- **Pyright**:
  - [Official Documentation](https://github.com/microsoft/pyright)
- **AWS Services**:
  - [Amazon EKS](https://aws.amazon.com/eks/)
  - [Amazon VPC](https://aws.amazon.com/vpc/)
  - [AWS IAM](https://aws.amazon.com/iam/)
  - [AWS KMS](https://aws.amazon.com/kms/)
  - [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/)
- **Fluent Bit**:
  - [Official Documentation](https://docs.fluentbit.io/)
