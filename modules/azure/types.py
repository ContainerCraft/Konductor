# pulumi/modules/aws/types.py

"""
AWS Module Configuration Types

Defines data classes for AWS module configurations using Pydantic for type safety and validation.
Ensures integration of compliance configurations.

Classes:
- IAMUserConfig: IAM user configuration.
- ControlTowerConfig: AWS Control Tower configuration.
- TenantAccountConfig: Tenant account configuration.
- GlobalTags: Global tags for resources.
- AWSConfig: Aggregated AWS configurations, including compliance settings.
- EksNodeGroupConfig: Configuration for EKS node groups.
- EksAddonConfig: Configuration for EKS add-ons.
- EksConfig: Configuration for EKS clusters.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any, Union, TypedDict, Tuple, TYPE_CHECKING, Protocol
from pydantic import BaseModel, Field, validator, root_validator
from core.types import ComplianceConfig
import pulumi
import pulumi_aws as aws
import ipaddress
from .organization import AWSOrganization
from .security import SecurityManager
from .networking import NetworkManager
from .resources import ResourceManager

if TYPE_CHECKING:
    from .security import SecurityManager
    from .networking import NetworkManager
    from .organization import AWSOrganization
    from .resources import ResourceManager
    from .iam import IAMManager
    from .eks import EksManager
    from .types import AWSConfig, AWSManagers
    from .provider import AWSProvider

class IAMUserConfig(BaseModel):
    """Configuration for an IAM User in AWS."""

    name: str = Field(..., description="Name of the IAM user.")
    email: str = Field(..., description="Email address of the IAM user.")
    groups: List[str] = Field(
        default_factory=list, description="IAM groups the user belongs to."
    )
    policies: List[str] = Field(
        default_factory=list, description="IAM policy ARNs attached to the user."
    )
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Tags to apply to the IAM user."
    )
    path: Optional[str] = Field(default="/", description="IAM user path.")
    permissions_boundary: Optional[str] = Field(
        None, description="ARN of the policy to set as permissions boundary."
    )

class SecurityGroupRule(BaseModel):
    """Configuration for a security group rule."""
    type: str = Field(..., description="Rule type (ingress/egress)")
    protocol: str = Field(..., description="Network protocol")
    from_port: int = Field(..., description="Starting port range")
    to_port: int = Field(..., description="Ending port range")
    cidr_blocks: Optional[List[str]] = Field(None, description="CIDR blocks")
    security_group_id: Optional[str] = Field(None, description="Source/destination security group")
    description: Optional[str] = Field(None, description="Rule description")

class NetworkConfig(BaseModel):
    """Network configuration for AWS resources."""
    vpc_cidr: str = Field(..., description="VPC CIDR block")
    subnet_cidrs: Dict[str, List[str]] = Field(
        ..., description="Subnet CIDR blocks by type (public/private)"
    )
    availability_zones: List[str] = Field(..., description="Availability zones to use")
    enable_nat_gateway: bool = Field(True, description="Enable NAT Gateway")
    enable_vpn_gateway: bool = Field(False, description="Enable VPN Gateway")
    enable_flow_logs: bool = Field(True, description="Enable VPC Flow Logs")
    tags: Dict[str, str] = Field(default_factory=dict, description="Network resource tags")

    @validator("vpc_cidr")
    def validate_vpc_cidr(cls, v):
        try:
            ipaddress.ip_network(v)
        except ValueError:
            raise ValueError(f"Invalid VPC CIDR: {v}")
        return v

class ControlTowerConfig(BaseModel):
    """Configuration for AWS Control Tower."""

    enabled: bool = Field(default=False, description="Enable AWS Control Tower.")
    organizational_unit_name: str = Field(
        default="LandingZone", description="Name of the Organizational Unit."
    )
    execution_role_name: str = Field(
        default="AWSControlTowerExecution", description="Name of the execution role."
    )
    execution_role_arn: Optional[str] = Field(
        None, description="ARN of the execution role."
    )
    admin_role_name: str = Field(
        default="AWSControlTowerAdmin", description="Name of the admin role."
    )
    admin_role_arn: Optional[str] = Field(None, description="ARN of the admin role.")
    audit_role_name: str = Field(
        default="AWSControlTowerAudit", description="Name of the audit role."
    )
    audit_role_arn: Optional[str] = Field(None, description="ARN of the audit role.")
    log_archive_bucket: Optional[str] = Field(
        None, description="Name of the log archive bucket."
    )

    @validator("enabled", pre=True)
    def validate_control_tower_fields(cls, v, values):
        if v:
            required_fields = ["execution_role_arn", "admin_role_arn"]
            missing = [field for field in required_fields if not values.get(field)]
            if missing:
                raise ValueError(
                    f"Missing fields for Control Tower: {', '.join(missing)}"
                )
        return v

class SecurityConfig(BaseModel):
    """Security configuration for AWS resources."""
    enable_security_hub: bool = Field(True, description="Enable Security Hub")
    enable_guard_duty: bool = Field(True, description="Enable GuardDuty")
    enable_config: bool = Field(True, description="Enable AWS Config")
    enable_cloudtrail: bool = Field(True, description="Enable CloudTrail")
    kms_deletion_window: int = Field(30, description="KMS key deletion window in days")
    enable_key_rotation: bool = Field(True, description="Enable KMS key rotation")
    security_group_rules: List[SecurityGroupRule] = Field(
        default_factory=list,
        description="Security group rules"
    )

    @validator("security_group_rules")
    def validate_security_rules(cls, v):
        for rule in v:
            if rule.type not in ["ingress", "egress"]:
                raise ValueError(f"Invalid rule type: {rule.type}")
            if not rule.cidr_blocks and not rule.security_group_id:
                raise ValueError("Either CIDR blocks or security group ID required")
        return v

class TenantAccountConfig(BaseModel):
    """Configuration for a Tenant Account within AWS."""

    name: str = Field(..., description="Name of the tenant account.")
    email: str = Field(
        ..., description="Email address associated with the tenant account."
    )
    administrators: List[str] = Field(
        default_factory=list, description="Administrators of the tenant account."
    )
    users: List[str] = Field(
        default_factory=list, description="Users of the tenant account."
    )
    features: List[str] = Field(
        default_factory=list, description="Enabled features for the tenant account."
    )
    network: Optional[NetworkConfig] = Field(
        None, description="Network configuration for the tenant."
    )
    security: Optional[SecurityConfig] = Field(
        None, description="Security configuration for the tenant."
    )
    aws: Dict[str, Any] = Field(
        default_factory=dict,
        description="AWS-specific configuration for the tenant account.",
    )
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Tags for resources in the tenant account."
    )

class GlobalTags(BaseModel):
    """Global tags to apply to all AWS resources."""

    project: str = Field(default="konductor", description="Project name.")
    managed_by: str = Field(
        default="NASA_SCIP_OPERATIONS", description="Managed by identifier."
    )
    environment: str = Field(
        default="production", description="Environment identifier."
    )
    cost_center: Optional[str] = Field(None, description="Cost center identifier.")
    data_classification: Optional[str] = Field(
        None, description="Data classification level."
    )

class BackupConfig(BaseModel):
    """Configuration for AWS backup policies."""
    enabled: bool = Field(True, description="Enable AWS Backup")
    retention_days: int = Field(30, description="Backup retention period")
    schedule_expression: str = Field("cron(0 5 ? * * *)", description="Backup schedule")
    copy_actions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Cross-region/account copy actions"
    )

    @validator("retention_days")
    def validate_retention_days(cls, v):
        if v < 1:
            raise ValueError("Retention days must be positive")
        return v

    @validator("schedule_expression")
    def validate_schedule(cls, v):
        if not v.startswith("cron(") or not v.endswith(")"):
            raise ValueError("Invalid cron expression format")
        return v

class MonitoringConfig(BaseModel):
    """Configuration for AWS monitoring."""
    enable_enhanced_monitoring: bool = Field(True, description="Enable enhanced monitoring")
    metrics_collection_interval: int = Field(60, description="Metrics collection interval")
    log_retention_days: int = Field(90, description="Log retention period")
    alarm_notification_topic: Optional[str] = Field(None, description="SNS topic for alarms")

class EksNodeGroupConfig(BaseModel):
    """Configuration for EKS node groups."""
    name: str = Field(..., description="Node group name")
    instance_type: str = Field(default="t3.medium", description="EC2 instance type")
    desired_size: int = Field(default=2, description="Desired number of nodes")
    min_size: int = Field(default=1, description="Minimum number of nodes")
    max_size: int = Field(default=3, description="Maximum number of nodes")
    disk_size: int = Field(default=50, description="Node disk size in GB")
    ami_type: str = Field(default="AL2_x86_64", description="AMI type")
    capacity_type: str = Field(default="ON_DEMAND", description="Capacity type (ON_DEMAND/SPOT)")
    labels: Dict[str, str] = Field(default_factory=dict, description="Kubernetes labels")
    taints: Optional[List[Dict[str, str]]] = Field(None, description="Kubernetes taints")

class EksAddonConfig(BaseModel):
    """Configuration for EKS add-ons."""
    vpc_cni: bool = Field(default=True, description="Enable AWS VPC CNI")
    coredns: bool = Field(default=True, description="Enable CoreDNS")
    kube_proxy: bool = Field(default=True, description="Enable kube-proxy")
    aws_load_balancer_controller: bool = Field(default=True, description="Enable AWS Load Balancer Controller")
    cluster_autoscaler: bool = Field(default=True, description="Enable Cluster Autoscaler")
    metrics_server: bool = Field(default=True, description="Enable Metrics Server")
    aws_for_fluent_bit: bool = Field(default=True, description="Enable AWS for Fluent Bit")

class EksConfig(BaseModel):
    """Configuration for EKS clusters."""
    enabled: bool = Field(default=False, description="Enable EKS deployment")
    cluster_name: str = Field(..., description="EKS cluster name")
    kubernetes_version: str = Field(default="1.26", description="Kubernetes version")
    endpoint_private_access: bool = Field(default=True, description="Enable private endpoint")
    endpoint_public_access: bool = Field(default=False, description="Enable public endpoint")
    node_groups: List[EksNodeGroupConfig] = Field(default_factory=list, description="Node group configurations")
    addons: EksAddonConfig = Field(default_factory=EksAddonConfig, description="Add-on configurations")
    enable_irsa: bool = Field(default=True, description="Enable IAM Roles for Service Accounts")
    enable_secrets_encryption: bool = Field(default=True, description="Enable secrets encryption")
    enable_vpc_cni_prefix_delegation: bool = Field(default=True, description="Enable VPC CNI prefix delegation")

    @validator("kubernetes_version")
    def validate_k8s_version(cls, v):
        valid_versions = ["1.24", "1.25", "1.26", "1.27"]
        if v not in valid_versions:
            raise ValueError(f"Invalid Kubernetes version: {v}")
        return v

    @validator("node_groups")
    def validate_node_groups(cls, v):
        if not v:
            raise ValueError("At least one node group required")
        return v

class AWSConfig(BaseModel):
    """Aggregated configuration class for AWS module settings."""

    enabled: bool = Field(default=True, description="Enable the AWS module.")
    profile: str = Field(default="main", description="AWS CLI profile to use.")
    region: str = Field(default="us-west-2", description="AWS region for deployment.")
    account_id: str = Field(..., description="AWS account ID.")
    bucket: str = Field(..., description="Name of the S3 bucket for state storage.")
    control_tower: ControlTowerConfig = Field(
        default_factory=ControlTowerConfig,
        description="AWS Control Tower configuration.",
    )
    iam_users: List[IAMUserConfig] = Field(
        default_factory=list, description="IAM user configurations."
    )
    landingzones: List[TenantAccountConfig] = Field(
        default_factory=list, description="Tenant account configurations."
    )
    network: NetworkConfig = Field(
        ..., description="Network configuration."
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration."
    )
    backup: BackupConfig = Field(
        default_factory=BackupConfig,
        description="Backup configuration."
    )
    monitoring: MonitoringConfig = Field(
        default_factory=MonitoringConfig,
        description="Monitoring configuration."
    )
    global_tags: GlobalTags = Field(
        default_factory=GlobalTags, description="Global tags for all resources."
    )
    compliance: ComplianceConfig = Field(
        default_factory=ComplianceConfig, description="Compliance configuration."
    )
    version: str = Field(
        default="0.0.1", description="Version of the local AWS module."
    )

    @validator("region")
    def validate_region(cls, v):
        valid_regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
        if v not in valid_regions:
            raise ValueError(f"Invalid AWS region: {v}")
        return v

    @root_validator
    def validate_network_config(cls, values):
        """Validate network configuration."""
        if "network" in values:
            network = values["network"]
            if len(network.availability_zones) < 2:
                raise ValueError("At least 2 availability zones required")
        return values

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "AWSConfig":
        """Merges user configuration with defaults, handling compliance integration."""
        aws_specific_keys = {k for k in user_config.keys() if k != "compliance"}
        compliance_config = user_config.get("compliance", {})
        aws_config = {k: user_config[k] for k in aws_specific_keys}

        # Build compliance configuration
        compliance = ComplianceConfig.merge(compliance_config)
        aws_config["compliance"] = compliance

        return cls(**aws_config)

class ResourceManagerProtocol(Protocol):
    def deploy_resources(self) -> dict[str, Any]: ...

class AWSManagers(TypedDict):
    organization: AWSOrganization
    security: SecurityManager
    networking: NetworkManager
    resources: ResourceManagerProtocol

def validate_config(config: AWSConfig) -> None:
    """
    Validates the AWS configuration.

    Args:
        config: AWS configuration to validate.

    Raises:
        ValueError: If configuration is invalid.
    """
    if not config.account_id:
        raise ValueError("AWS account ID is required")

    if not config.region:
        raise ValueError("AWS region is required")

    if config.control_tower.enabled:
        if not config.control_tower.execution_role_arn:
            raise ValueError("Control Tower execution role ARN is required when enabled")

    # Validate tenant configurations
    if config.landingzones:
        for tenant in config.landingzones:
            if not tenant.email:
                raise ValueError(f"Email is required for tenant account {tenant.name}")



def validate_module_exports(
    version: str,
    resource: pulumi.Resource,
    outputs: Dict[str, Any]
) -> bool:
    """
    Validates module exports against required outputs.

    Args:
        version: Module version string
        resource: Main infrastructure resource
        outputs: Dictionary of outputs to validate

    Returns:
        bool: True if all required outputs are present
    """
    required_outputs = {
        "ops_data_bucket": "S3 bucket for operational data",
        "organization": "AWS Organization ID",
        "organization_arn": "AWS Organization ARN",
        "vpc_id": "Primary VPC ID",
        "subnet_ids": "List of subnet IDs",
        "security_groups": "Map of security group IDs",
        "kms_keys": "Map of KMS key ARNs",
        "iam_roles": "Map of IAM role ARNs"
    }

    missing = [key for key in required_outputs if key not in outputs]
    if missing:
        pulumi.log.warn(f"Missing required outputs: {', '.join(missing)}")
        return False

    return True
