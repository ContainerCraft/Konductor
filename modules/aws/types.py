# ./modules/aws/types.py
"""AWS Module Configuration Types"""

from __future__ import annotations
from typing import List, Dict, Optional, Any, TypedDict
from pydantic import BaseModel, Field, validator
from ..core.types import ComplianceConfig, GlobalMetadata
import pulumi_aws as aws


class IAMUserConfig(BaseModel):
    """Configuration for an IAM User in AWS."""

    name: str = Field(..., description="Name of the IAM user.")
    email: str = Field(..., description="Email address of the IAM user.")
    groups: List[str] = Field(default_factory=list)
    policies: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)
    path: Optional[str] = Field(default="/")
    permissions_boundary: Optional[str] = Field(None)


class NetworkConfig(BaseModel):
    """Network configuration for AWS resources."""

    vpc_cidr: str = Field(default="10.0.0.0/16", description="VPC CIDR block")
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
    tags: Dict[str, str] = Field(default_factory=dict)

    @validator("vpc_cidr")
    def validate_vpc_cidr(cls, v):
        try:
            from ipaddress import ip_network

            ip_network(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid VPC CIDR: {v}")


class SecurityConfig(BaseModel):
    """Security configuration for AWS resources."""

    enable_security_hub: bool = Field(True)
    enable_guard_duty: bool = Field(True)
    enable_config: bool = Field(True)
    enable_cloudtrail: bool = Field(True)
    kms_deletion_window: int = Field(30)
    enable_key_rotation: bool = Field(True)


class AWSProviderConfig(TypedDict):
    """AWS Provider configuration."""

    region: str
    profile: Optional[str]
    access_key_id: Optional[str]
    secret_access_key: Optional[str]
    tags: Dict[str, str]


class AWSConfig(BaseModel):
    """AWS Module configuration."""

    enabled: bool = Field(default=True)
    profile: Optional[str] = Field(default=None)
    region: str = Field(default="us-west-2")
    account_id: Optional[str] = Field(default=None)
    bucket: Optional[str] = Field(default=None)
    network: Optional[NetworkConfig] = Field(default_factory=NetworkConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)
    tags: Dict[str, str] = Field(default_factory=dict)

    @validator("region")
    def validate_region(cls, v):
        valid_regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
        if v not in valid_regions:
            raise ValueError(f"Invalid AWS region: {v}")
        return v

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "AWSConfig":
        """Merge user configuration with defaults."""
        aws_specific_keys = {k for k in user_config.keys() if k != "compliance"}
        compliance_config = user_config.get("compliance", {})
        aws_config = {k: user_config[k] for k in aws_specific_keys}

        if "network" not in aws_config:
            aws_config["network"] = NetworkConfig().model_dump()

        compliance = ComplianceConfig.merge(compliance_config)
        aws_config["compliance"] = compliance
        return cls(**aws_config)


class AWSModuleConfig(BaseModel):
    region: str = Field(..., description="AWS region")
    profile: str = Field(None, description="AWS profile")
    # TODO: Add other AWS-specific configuration fields


class AWSGlobalMetadata(GlobalMetadata):
    aws_account_id: str
    aws_user_id: str
    aws_arn: str
    # TODO: Complete implementation. Additional AWS-specific metadata fields can be added here


def collect_module_metadata() -> AWSGlobalMetadata:
    caller_identity = aws.get_caller_identity()

    return AWSGlobalMetadata(
        aws_account_id=caller_identity.account_id,
        aws_user_id=caller_identity.user_id,
        aws_arn=caller_identity.arn,
        # Add other metadata as needed
    )


class TenantAccountConfig(BaseModel):
    """Configuration for an AWS tenant account."""

    name: str = Field(..., description="Name of the tenant account")
    email: str = Field(..., description="Email address for the account root user")
    organizational_unit: Optional[str] = Field(None, description="OU to place the account in")
    tags: Dict[str, str] = Field(default_factory=dict)
