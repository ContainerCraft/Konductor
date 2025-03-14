# ./src/aws/types/__init__.py
"""
AWS Module Configuration Types (consolidated revision)

This refactored module defines all AWS-specific configuration and data types in a single file,
leveraging the core module types for consistency and maintainability.

Key Improvements:
- Exclusive use of Pydantic models, no TypedDict usage.
- Centralized metadata handling via CommonMetadataFields from the core module.
- Reuse of ComplianceConfig and other shared models from the core module.
- Strict typing and validation for all fields.
- Removal of redundancy and unused code snippets.
- Aligned with core module design principles.

Conventions and Requirements:
- Strict typing with Pyright in strict mode.
- No broad `except Exception` unless re-raised after logging.
- Security, compliance, and maintainability are priorities.
- No hardcoded credentials or secrets.
- PEP 8 and PEP 257 compliance.
"""


from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator
import os

from src.core.types import (
    BaseConfigModel,
    CommonMetadataFields,
    ComplianceConfig,
    GlobalMetadata,
)


class SecurityConfig(BaseModel):
    """
    Security configuration for AWS resources.

    Attributes:
        enable_security_hub: Enable AWS Security Hub.
        enable_guard_duty: Enable AWS GuardDuty.
        enable_config: Enable AWS Config.
        enable_cloudtrail: Enable AWS CloudTrail.
        kms_deletion_window: KMS key deletion window in days.
        enable_key_rotation: Enable KMS key rotation.
        metadata: CommonMetadataFields for consistent tagging.
    """

    enable_security_hub: bool = Field(default=True)
    enable_guard_duty: bool = Field(default=True)
    enable_config: bool = Field(default=True)
    enable_cloudtrail: bool = Field(default=True)
    kms_deletion_window: int = Field(default=30)
    enable_key_rotation: bool = Field(default=True)
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)


class NetworkConfig(BaseModel):
    """
    Network configuration for AWS resources.

    Attributes:
        vpc_cidr: CIDR block for the VPC.
        subnet_cidrs: Dictionary mapping subnet type to a list of CIDRs.
        availability_zones: List of availability zones.
        enable_nat_gateway: Whether to deploy a NAT gateway.
        enable_vpn_gateway: Whether to deploy a VPN gateway.
        enable_flow_logs: Whether to enable VPC Flow Logs.
        metadata: CommonMetadataFields for resource tagging.
    """

    vpc_cidr: str = Field(default="10.0.0.0/16")
    subnet_cidrs: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "public": ["10.0.1.0/24", "10.0.2.0/24"],
            "private": ["10.0.3.0/24", "10.0.4.0/24"],
        }
    )
    availability_zones: List[str] = Field(default_factory=lambda: ["us-east-1a", "us-east-1b"])
    enable_nat_gateway: bool = Field(default=True)
    enable_vpn_gateway: bool = Field(default=False)
    enable_flow_logs: bool = Field(default=True)
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)

    @validator("vpc_cidr")
    def validate_vpc_cidr(cls, v):
        from ipaddress import ip_network

        try:
            ip_network(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid VPC CIDR: {v}")


class IAMUserConfig(BaseModel):
    """
    Configuration for an IAM User in AWS.

    Attributes:
        name: Name of the IAM user.
        email: Email address of the IAM user.
        groups: List of IAM groups to associate the user with.
        policies: List of IAM policy ARNs to attach to the user.
        path: The path under which the user is created.
        permissions_boundary: ARN of a permissions boundary policy.
        metadata: CommonMetadataFields for tagging.
    """

    name: str
    email: str
    groups: List[str] = Field(default_factory=list)
    policies: List[str] = Field(default_factory=list)
    path: str = Field(default="/")
    permissions_boundary: Optional[str] = None
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)


class EksNodeGroupConfig(BaseModel):
    """
    Configuration for EKS node groups.

    Attributes:
        name: Name of the node group.
        instance_types: List of EC2 instance types for the node group.
        scaling_config: Scaling configuration dict.
        subnet_ids: Optional list of subnet IDs for the node group.
        metadata: CommonMetadataFields for consistent tagging.
    """

    name: str
    instance_types: List[str] = Field(default_factory=lambda: ["t3.medium"])
    scaling_config: Dict[str, int] = Field(
        default_factory=lambda: {
            "desired_size": 2,
            "max_size": 4,
            "min_size": 1,
        }
    )
    subnet_ids: Optional[List[str]] = None
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)


class EksClusterConfig(BaseModel):
    """
    Configuration for an EKS cluster.

    Attributes:
        enabled: Whether the EKS cluster is enabled.
        name: Name of the EKS cluster.
        version: Kubernetes version for the EKS cluster.
        subnet_ids: Optional subnets for the cluster.
        endpoint_private_access: Whether private endpoint access is enabled.
        endpoint_public_access: Whether public endpoint access is enabled.
        node_groups: List of EksNodeGroupConfig instances.
        metadata: CommonMetadataFields for tagging and annotation.
    """

    enabled: bool = Field(default=True)
    name: str
    version: str = Field(default="1.29")
    subnet_ids: Optional[List[str]] = None
    endpoint_private_access: bool = Field(default=True)
    endpoint_public_access: bool = Field(default=True)
    node_groups: List[EksNodeGroupConfig] = Field(default_factory=list)
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)

    @validator("version")
    def validate_version(cls, v):
        valid_versions = ["1.29", "1.28", "1.27", "1.26", "1.25"]
        if v not in valid_versions:
            raise ValueError(f"Invalid EKS version: {v}. Must be one of {valid_versions}")
        return v


class EksConfig(BaseModel):
    """
    High-level EKS configuration aggregating one or more clusters.

    Attributes:
        enabled: Whether EKS is enabled at all.
        clusters: List of EksClusterConfig instances.
    """

    enabled: bool = Field(default=False)
    clusters: List[EksClusterConfig] = Field(default_factory=list)


class TenantAccountConfig(BaseModel):
    """
    Configuration for an AWS tenant account.

    Attributes:
        name: Name of the tenant account.
        email: Email for the account root user.
        organizational_unit: Optional OU to place the account in.
        metadata: CommonMetadataFields for tagging.
    """

    name: str
    email: str
    organizational_unit: Optional[str] = None
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields)


class AWSProviderMetadata(BaseModel):
    """
    AWS provider metadata.

    Attributes:
        account_id: AWS account ID.
        user_id: AWS user ID.
        arn: AWS ARN of the caller identity.
        region: AWS region in use.
    """

    account_id: str
    user_id: str
    arn: str
    region: str


class AWSGlobalMetadata(GlobalMetadata):
    """
    AWS Global metadata extension.

    Attributes:
        aws_account_id: AWS account ID (optional).
        aws_user_id: AWS user ID (optional).
        aws_arn: AWS ARN (optional).
    """

    aws_account_id: Optional[str] = None
    aws_user_id: Optional[str] = None
    aws_arn: Optional[str] = None


class AWSConfig(BaseConfigModel):
    """
    AWS Module configuration.

    Inherits from BaseConfigModel to leverage `enabled`, `metadata`, etc.

    Attributes:
        profile: Optional AWS profile to use.
        region: AWS region.
        account_id: Optional AWS account ID.
        bucket: Optional S3 bucket name.
        network: NetworkConfig for AWS networking resources.
        security: SecurityConfig for AWS security services.
        compliance: ComplianceConfig for compliance and governance.
        eks: Optional EKS configuration (EksConfig).
    """

    enabled: bool = Field(default=True)
    profile: Optional[str] = Field(default=os.getenv("AWS_PROFILE") or None)
    region: str = Field(default="us-east-1")
    account_id: Optional[str] = None
    bucket: Optional[str] = None
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig.create_default)
    eks: Optional[EksConfig] = None

    @validator("region")
    def validate_region(cls, v):
        valid_regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
        if v not in valid_regions:
            raise ValueError(f"Invalid AWS region: {v}")
        return v


__all__ = [
    "IAMUserConfig",
    "NetworkConfig",
    "SecurityConfig",
    "EksNodeGroupConfig",
    "EksClusterConfig",
    "EksConfig",
    "AWSConfig",
    "TenantAccountConfig",
    "AWSProviderMetadata",
    "AWSGlobalMetadata",
]
