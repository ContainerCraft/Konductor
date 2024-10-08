# pulumi/modules/aws/types.py

"""
This module defines the data classes for the AWS module.

This module defines the Pydantic models for the AWS module configurations.
These models ensure type safety and validation of the configuration data.

The module defines the following data classes:

    - IAMUserConfig: Defines the IAM user configuration.
    - ControlTowerConfig: Defines the Control Tower configuration.
    - AWSConfig: Defines the AWS configuration.
    - TenantAccountConfig: Defines the tenant account configuration.
    - GlobalTags: Defines the global tags for resources.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class IAMUserConfig(BaseModel):
    """
    Configuration for an IAM User.
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
    Configuration for a Tenant Account.
    """
    name: str = Field(..., description="Name of the tenant account.")
    email: str = Field(..., description="Email address associated with the tenant account.")
    administrators: List[str] = Field(default_factory=list, description="List of administrators for the tenant account.")
    users: List[str] = Field(default_factory=list, description="List of users for the tenant account.")
    features: List[str] = Field(default_factory=list, description="List of features enabled for the tenant account.")
    aws: Dict[str, str] = Field(default_factory=dict, description="AWS-specific configuration for the tenant account.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags to apply to resources in the tenant account.")


class GlobalTags(BaseModel):
    """
    Global tags to apply to all resources.
    """
    project: str = Field(default="konductor", description="Project name.")
    managed_by: str = Field(default="NASA_SCIP_OPERATIONS", description="Managed by identifier.")


class AWSConfig(BaseModel):
    """
    Configuration for the AWS module.
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
    #secret_access_key: str = Field(..., description="AWS secret access key.")
    #access_key_id: str = Field(..., description="AWS access key ID.")

    #@validator('secret_access_key', pre=True, always=True)
    #def mask_secret_access_key(cls, v):
    #    """
    #    Mask the secret access key for security purposes.
    #    """
    #    # This is a placeholder. In real scenarios, secrets should be handled securely.
    #    if not v:
    #        raise ValueError("secret_access_key must be provided")
    #    return v

    #@validator('access_key_id', pre=True, always=True)
    #def validate_access_key_id(cls, v):
    #    """
    #    Validate the access key ID format.
    #    """
    #    if not v:
    #        raise ValueError("access_key_id must be provided")
    #    # Add regex or other validation logic if necessary
    #    return v

    @validator('region')
    def validate_region(cls, v):
        """
        Validate that the region is a valid AWS region.
        """
        valid_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-central-1', 'eu-west-1', 'ap-southeast-1', 'ap-southeast-2',
            # Add more regions as needed
        ]
        if v not in valid_regions:
            raise ValueError(f"Invalid AWS region: {v}")
        return v

    @validator('control_tower')
    def validate_control_tower_config(cls, v):
        """
        Validate Control Tower configuration if enabled.
        """
        if v.enabled:
            required_fields = ['execution_role_arn', 'admin_role_arn', 'audit_role_arn', 'log_archive_bucket']
            missing_fields = [field for field in required_fields if not getattr(v, field)]
            if missing_fields:
                raise ValueError(f"Control Tower is enabled but missing fields: {', '.join(missing_fields)}")
        return v

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> 'AWSConfig':
        """
        Merges user-provided AWS configuration with default values.

        Args:
            user_config (Dict[str, Any]): The user-provided AWS configuration.

        Returns:
            AWSConfig: The merged AWS configuration.
        """
        return cls(**user_config)
