# ./modules/aws/eks/__init__.py
"""AWS EKS Management Module

This module provides an opinionated way to manage and deploy an EKS cluster and related
infrastructure using Pulumi.

Features:
- Creates a VPC, subnets, route tables, and NAT gateway resources suitable for EKS
- Sets up IAM roles for the EKS cluster and node groups
- Provisions the EKS cluster and node groups
- Generates IAM-based kubeconfig
- Creates Pulumi Kubernetes provider
- Optionally deploys test workloads
"""

from .deployment import EksManager
from .types import (
    EksClusterConfig,
    EksNodeGroupConfig,
    NetworkingConfig,
    EksConfig,
    NodeGroupConfig,
    ClusterConfig,
)

__all__ = [
    "EksManager",
    "EksClusterConfig",
    "EksNodeGroupConfig",
    "NetworkingConfig",
    "EksConfig",
    "NodeGroupConfig",
    "ClusterConfig",
]
