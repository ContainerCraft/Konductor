# ./modules/aws/config.py

"""
AWS Module Configuration

Handles initialization and configuration of AWS resources and providers within the Pulumi stack.
Includes functions to load settings, initialize the provider, and propagate compliance and Git metadata as tags.

Functions:
- load_aws_config: Loads and parses the AWS configuration.
- initialize_aws_provider: Initializes the AWS provider with credentials and region.
- generate_tags: Creates global tags including compliance and Git metadata.
- generate_global_transformations: Registers a transformation to apply tags to all resources.
- load_tenant_account_configs: Loads tenant account configurations.
"""

import os
import json
from typing import Dict, Any, Optional
import pulumi
from pulumi import log, Config, ResourceTransformationResult, ResourceTransformationArgs
from pulumi_aws import Provider
from .types import AWSConfig, TenantAccountConfig, AWSModuleConfig
from ..core.types import ComplianceConfig
from pydantic import BaseModel, Field, ValidationError

# Constants
MODULE_NAME = "aws"
MODULE_VERSION = "0.0.1"

TAGGABLE_RESOURCES = [
    "aws:s3/bucket:Bucket",
    "aws:ec2/vpc:Vpc",
    "aws:ec2/subnet:Subnet",
    "aws:ec2/instance:Instance",
    "aws:iam/role:Role",
    "aws:rds/instance:Instance",
]

DEFAULT_MODULE_CONFIG = {
    "enabled": True,
    "version": "latest",
    "config": {"region": "us-east-1"},
    "compliance": {
        "fisma": {
            "enabled": False,
            "level": "low",
            "mode": "strict",
            "ato": {"id": None, "authorized": None, "eol": None},
        }
    },
}


def validate_config(raw_config: dict) -> AWSModuleConfig:
    try:
        return AWSModuleConfig(**raw_config)
    except ValidationError as e:
        raise ValueError(f"AWS module configuration error: {e}")


def initialize_aws_provider(config: AWSConfig) -> Provider:
    """
    Initializes the AWS provider with the supplied configuration.

    Args:
        config (AWSConfig): AWS configuration with provider details.

    Returns:
        Provider: An initialized AWS Provider for resource management.
    """
    aws_config = pulumi.Config("aws")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID") or aws_config.get("access_key_id")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or aws_config.get("secret_access_key")
    profile = os.getenv("AWS_PROFILE") or config.profile

    return Provider(
        "awsProvider",
        access_key=aws_access_key,
        secret_key=aws_secret_key,
        profile=profile,
        region=config.region,
    )


def generate_global_transformations(global_tags: Dict[str, str]) -> None:
    """
    Registers a global transformation to apply tags to AWS resources that support tagging.

    Args:
        global_tags (Dict[str, str]): The global tags to apply.
    """

    def global_transform(
        args: ResourceTransformationArgs,
    ) -> Optional[ResourceTransformationResult]:
        resource_type = args.type_

        # Check if the resource type is in the list of taggable resources
        if resource_type in TAGGABLE_RESOURCES:
            props = args.props.copy()
            opts = args.opts

            # Merge existing tags with global tags
            tags = props.get("tags") or {}
            tags.update(global_tags)
            props["tags"] = tags

            return ResourceTransformationResult(props, opts)
        else:
            # Do not modify resources that do not support tags
            return None

    pulumi.runtime.register_stack_transformation(global_transform)


def generate_tags(config: AWSConfig, compliance_config: ComplianceConfig, git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates tags for AWS resources, including compliance and Git metadata.

    Args:
        config (AWSConfig): AWS configuration object.
        compliance_config (ComplianceConfig): Compliance configuration.
        git_info (Dict[str, str]): Git repository and commit information.

    Returns:
        Dict[str, str]: Tags to apply to AWS resources.
    """
    # Generate compliance and Git labels
    compliance_labels = generate_compliance_labels(compliance_config)
    git_labels = generate_git_labels(git_info)

    # Combine all labels into global tags
    aws_module_tags = {
        **compliance_labels,
        **git_labels,
        "iac_module_name": MODULE_NAME,
        "iac_module_version": MODULE_VERSION,
    }

    # Log generated tags for visibility
    log.info(f"Generated AWS tags: {json.dumps(aws_module_tags, indent=2)}")

    # Register the global transformation
    generate_global_transformations(aws_module_tags)

    return aws_module_tags


def load_aws_config() -> AWSConfig:
    """
    Loads the AWS module configuration using Pulumi Config.

    Returns:
        AWSConfig: Parsed AWS configuration object.

    Raises:
        ValueError: If there's an issue with the AWS configuration format.
    """
    config = Config()
    aws_config_dict = config.get_object("aws") or {}
    compliance_config_dict = config.get_object("compliance") or {}

    # Include the compliance config into the aws_config_dict
    aws_config_dict["compliance"] = compliance_config_dict

    try:
        aws_config = AWSConfig.merge(aws_config_dict)
    except Exception as e:
        log.error(f"Invalid AWS configuration: {e}")
        raise

    return aws_config


def load_tenant_account_configs() -> Dict[str, TenantAccountConfig]:
    """
    Loads configurations for tenant accounts.

    Returns:
        Dict[str, TenantAccountConfig]: Configurations for each tenant account.
    """
    config = Config()
    aws_config_dict = config.get_object("aws") or {}
    tenant_accounts_list = aws_config_dict.get("landingzones", [])
    tenant_accounts = {}

    for tenant in tenant_accounts_list:
        try:
            tenant_config = TenantAccountConfig(**tenant)
            tenant_accounts[tenant_config.name] = tenant_config
        except Exception as e:
            log.warn(f"Invalid tenant account configuration for '{tenant.get('name', 'unknown')}': {e}")

    return tenant_accounts


def merge_configurations(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two configuration dictionaries with override taking precedence.

    Args:
        base_config: Base configuration dictionary.
        override_config: Override configuration dictionary.

    Returns:
        Dict[str, Any]: Merged configuration dictionary.
    """
    merged = base_config.copy()
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configurations(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_default_config() -> Dict[str, Any]:
    """
    Returns default AWS configuration settings.

    Returns:
        Dict[str, Any]: Default configuration dictionary.
    """
    return {
        "region": "us-west-2",
        "profile": "default",
        "control_tower": {
            "enabled": False,
            "organizational_unit_name": "LandingZone",
        },
        "global_tags": {
            "managed-by": "konductor",
            "environment": "production",
        },
    }


def load_environment_overrides() -> Dict[str, Any]:
    """
    Loads configuration overrides from environment variables.

    Returns:
        Dict[str, Any]: Configuration overrides from environment.
    """
    overrides = {}

    # Map environment variables to configuration keys
    env_mapping = {
        "AWS_REGION": "region",
        "AWS_PROFILE": "profile",
        "AWS_ACCOUNT_ID": "account_id",
    }

    for env_var, config_key in env_mapping.items():
        if value := os.getenv(env_var):
            overrides[config_key] = value

    return overrides


def setup_aws_configuration() -> AWSConfig:
    """
    Sets up the complete AWS configuration by combining defaults,
    Pulumi config, and environment variables.

    Returns:
        AWSConfig: Complete AWS configuration object.

    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    try:
        # Load configurations in order of precedence
        default_config = get_default_config()
        pulumi_config = load_aws_config()
        env_overrides = load_environment_overrides()

        # Merge configurations
        merged_config = merge_configurations(default_config, pulumi_config.dict())
        final_config = merge_configurations(merged_config, env_overrides)

        # Create and validate config object
        config = AWSConfig.merge(final_config)
        validate_config(config)

        return config

    except Exception as e:
        log.error(f"Failed to setup AWS configuration: {str(e)}")
        raise


def generate_compliance_labels(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance-related resource labels.

    Args:
        compliance_config: Compliance configuration object

    Returns:
        Dict[str, str]: Compliance labels
    """
    labels = {}

    if compliance_config.fisma.enabled:
        labels["compliance.fisma.enabled"] = "true"
        if compliance_config.fisma.level:
            labels["compliance.fisma.level"] = compliance_config.fisma.level

    if compliance_config.nist.enabled:
        labels["compliance.nist.enabled"] = "true"
        if compliance_config.nist.controls:
            labels["compliance.nist.controls"] = ",".join(compliance_config.nist.controls)

    return labels


def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates Git-related resource labels.

    Args:
        git_info: Git repository information

    Returns:
        Dict[str, str]: Git labels
    """
    return {
        "git.commit": git_info.get("commit_hash", "unknown"),
        "git.branch": git_info.get("branch_name", "unknown"),
        "git.repository": git_info.get("remote_url", "unknown"),
    }


class AWSModuleConfig(BaseModel):
    region: str = Field(..., description="AWS region to deploy resources")
    access_key_id: str = Field(None, description="AWS access key ID")
    secret_access_key: str = Field(None, description="AWS secret access key")
    bucket_name: str = Field(..., description="Name of the S3 bucket to create")
