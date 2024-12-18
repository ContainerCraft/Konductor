# ./modules/aws/types/components/eks/types.py
"""
EKS Component Types implemented in the AWS module EKS component submodule.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pulumi import ResourceOptions


@dataclass
class NetworkingConfig:
    """EKS networking configuration."""

    vpc_cidr: str = "10.0.0.0/16"
    azs: List[str] = field(default_factory=lambda: ["us-east-1a", "us-east-1b"])
    public_subnet_cidrs: List[str] = field(default_factory=list)
    private_subnet_cidrs: List[str] = field(default_factory=list)


@dataclass
class EksNodeGroupConfig:
    """Configuration for EKS node groups."""

    name: str = "default"
    instance_types: List[str] = field(default_factory=lambda: ["t3.medium"])
    scaling_config: Dict[str, int] = field(
        default_factory=lambda: {
            "desired_size": 2,
            "max_size": 4,
            "min_size": 1,
        }
    )
    subnet_ids: Optional[List[str]] = field(default=None)
    tags: Optional[Dict[str, str]] = field(default_factory=dict)


@dataclass
class EksClusterConfig:
    """Configuration for individual EKS cluster."""

    name: str
    version: str = "1.29"
    node_groups: List[EksNodeGroupConfig] = field(default_factory=list)
    endpoint_private_access: bool = True
    endpoint_public_access: bool = True
    subnet_ids: Optional[List[str]] = field(default=None)
    tags: Optional[Dict[str, str]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.node_groups:
            self.node_groups = [EksNodeGroupConfig(name=f"{self.name}-default")]


@dataclass
class EksConfig:
    """Root EKS configuration matching the Pulumi config structure."""

    enabled: bool = True
    clusters: List[EksClusterConfig] = field(default_factory=list)

    def __post_init__(self):
        if self.enabled and not self.clusters:
            raise ValueError("EKS is enabled but no clusters are configured")


@dataclass
class NodeGroupConfig:
    """Internal node group configuration."""

    name: str
    instance_types: List[str]
    scaling_config: Dict[str, int]
    subnet_ids: List[str]
    tags: Optional[Dict[str, str]] = field(default_factory=dict)
    opts: Optional[ResourceOptions] = None


@dataclass
class ClusterConfig:
    """Internal cluster configuration."""

    name: str
    version: str
    subnet_ids: List[str]
    tags: Optional[Dict[str, str]] = field(default_factory=dict)
    endpoint_private_access: bool = True
    endpoint_public_access: bool = True
