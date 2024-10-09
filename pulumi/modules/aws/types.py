# pulumi/modules/aws/types.py

"""
AWS Module Configuration Types

This module defines the data classes for AWS module configurations
using Pydantic for type safety and data validation. The classes ensure
integration of compliance configurations and eliminate configuration key warnings.

Data Classes:
- IAMUserConfig: Defines the IAM user configuration.
- ControlTowerConfig: Defines the Control Tower configuration.
- TenantAccountConfig: Defines the tenant account configuration.
- GlobalTags: Defines the global tags to apply to resources.
- AWSConfig: Aggregates AWS-specific configurations, including compliance settings.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from core.types import ComplianceConfig

class IAMUserConfig(BaseModel):
    """
    Configuration for an IAM User in AWS.
    """
    name: str = Field(..., description="Name of the IAM user.")
    email: str = Field(..., description="Email address of the IAM user.")
    groups: List[str] = Field(default_factory=list, description="List of IAM groups the user belongs to.")
    policies: List[str] = Field(default_factory=list, description="List of IAM policy ARNs attached to the user.")


class ControlTowerConfig(BaseModel):
    """
    Configuration for AWS Control Tower.
    """
    enabled: bool = Field(default=False, description="Enable or disable AWS Control Tower.")
    organizational_unit_name: str = Field(default="LandingZone", description="Name of the Organizational Unit.")
    execution_role_name: str = Field(default="AWSControlTowerExecution", description="Name of the execution role.")
    execution_role_arn: Optional[str] = Field(None, description="ARN of the execution role.")
    admin_role_name: str = Field(default="AWSControlTowerAdmin", description="Name of the admin role.")
    admin_role_arn: Optional[str] = Field(None, description="ARN of the admin role.")
    audit_role_name: str = Field(default="AWSControlTowerAudit", description="Name of the audit role.")
    audit_role_arn: Optional[str] = Field(None, description="ARN of the audit role.")
    log_archive_bucket: Optional[str] = Field(None, description="Name of the log archive bucket.")


class TenantAccountConfig(BaseModel):
    """
    Configuration for a Tenant Account within AWS.
    """
    name: str = Field(..., description="Name of the tenant account.")
    email: str = Field(..., description="Email address associated with the tenant account.")
    administrators: List[str] = Field(default_factory=list, description="Administrators of the tenant account.")
    users: List[str] = Field(default_factory=list, description="Users of the tenant account.")
    features: List[str] = Field(default_factory=list, description="Enabled features for the tenant account.")
    aws: Dict[str, str] = Field(default_factory=dict, description="AWS-specific configuration for the tenant account.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags to apply to resources in the tenant account.")


class GlobalTags(BaseModel):
    """
    Global tags to apply to all AWS resources.
    """
    project: str = Field(default="konductor", description="Project name.")
    managed_by: str = Field(default="NASA_SCIP_OPERATIONS", description="Managed by identifier.")


class AWSConfig(BaseModel):
    """
    Aggregated configuration class for AWS module settings.
    Integrates compliance configuration while removing key conflicts.
    """
    enabled: bool = Field(default=True, description="Enable or disable the AWS module.")
    profile: str = Field(default="main", description="AWS CLI profile to use.")
    region: str = Field(default="us-west-2", description="AWS region for resource deployment.")
    account_id: str = Field(..., description="AWS account ID.")
    bucket: str = Field(..., description="Name of the S3 bucket for state storage.")
    control_tower: ControlTowerConfig = Field(default_factory=ControlTowerConfig, description="AWS Control Tower configuration.")
    iam_users: List[IAMUserConfig] = Field(default_factory=list, description="List of IAM user configurations.")
    landingzones: List[TenantAccountConfig] = Field(default_factory=list, description="List of tenant account configurations.")
    global_tags: GlobalTags = Field(default_factory=GlobalTags, description="Global tags to apply to all resources.")
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig, description="Compliance configuration.")

    @validator('region')
    def validate_region(cls, v):
        valid_regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
        if v not in valid_regions:
            raise ValueError(f"Invalid AWS region: {v}")
        return v

    @validator('control_tower', always=True)
    def validate_control_tower_config(cls, v: ControlTowerConfig):
        if v.enabled:
            required_fields = ['execution_role_arn', 'admin_role_arn']
            missing_fields = [field for field in required_fields if not getattr(v, field, None)]
            if missing_fields:
                raise ValueError(f"Control Tower is enabled but missing fields: {', '.join(missing_fields)}")
        return v

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> 'AWSConfig':
        """
        Merges the user configuration with default settings, handling compliance integration.
        """
        # Separating AWS-specific and compliance-specific keys
        aws_keys = {k for k in user_config.keys() if k not in {'compliance'}}
        compliance_keys = user_config.get('compliance', {})

        filtered_config = {k: user_config[k] for k in aws_keys}  # AWS-specific subset
        compliance_config = ComplianceConfig.merge(compliance_keys)

        full_config = cls(**filtered_config)
        full_config.compliance = compliance_config

        return full_config
