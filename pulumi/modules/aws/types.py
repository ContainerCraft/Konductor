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
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from core.types import ComplianceConfig


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

    @validator("enabled", always=True)
    def validate_control_tower_fields(cls, v, values):
        if v:
            required_fields = ["execution_role_arn", "admin_role_arn"]
            missing = [field for field in required_fields if not values.get(field)]
            if missing:
                raise ValueError(
                    f"Missing fields for Control Tower: {', '.join(missing)}"
                )
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
