# konductor/pulumi/modules/aws/config.py

"""
AWS Module Configuration

This module handles the initialization and configuration of AWS resources and providers
within the Pulumi stack. It includes functions to load AWS-specific settings, initialize
the AWS provider, and propagate compliance and Git metadata as AWS resource tags.

The module defines the following functions:
    - load_aws_config: Loads and parses the AWS configuration.
    - initialize_aws_provider: Initializes the AWS provider with credentials and region.
    - generate_tags: Creates global tags including compliance and Git metadata.
    - load_tenant_account_configs: Loads tenant account configurations.
"""

import os
from typing import Dict, Any
import pulumi
from pulumi import log, Config
from pulumi_aws import Provider
from core.metadata import get_global_labels, generate_compliance_labels, generate_git_labels
from core.types import ComplianceConfig
from .types import AWSConfig, TenantAccountConfig

# Constants
MODULE_NAME = "aws"

def initialize_aws_provider(config: AWSConfig) -> Provider:
    """
    Initializes the AWS provider with the supplied configuration.

    Args:
        config (AWSConfig): The AWS configuration object with provider details.

    Returns:
        Provider: An initialized AWS Provider for resource management.
    """
    aws_config = pulumi.Config("aws")
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', aws_config.get("access_key_id"))
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', aws_config.get("secret_access_key"))
    profile = os.getenv('AWS_PROFILE', config.profile)

    return Provider(
        "awsProvider",
        access_key=aws_access_key,
        secret_key=aws_secret_key,
        profile=profile,
        region=config.region,
    )

def generate_tags(config: AWSConfig, compliance_config: ComplianceConfig, git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates tags for AWS resources, including compliance and Git metadata.

    Args:
        config (AWSConfig): The AWS configuration object.
        compliance_config (ComplianceConfig): The compliance configuration object.
        git_info (Dict[str, str]): Information about the Git repository and commit.

    Returns:
        Dict[str, str]: A dictionary containing key-value pairs of tags to apply to AWS resources.
    """
    global_labels = get_global_labels()
    compliance_labels = generate_compliance_labels(compliance_config)
    git_labels = generate_git_labels(git_info)

    aws_module_tags = {
        **global_labels,
        **compliance_labels,
        **git_labels,
        "iac_module_name": MODULE_NAME
    }
    pulumi.export("aws_module_tags", aws_module_tags)

    return aws_module_tags

def load_aws_config() -> AWSConfig:
    """
    Loads the AWS module configuration using Pulumi Config.

    Returns:
        AWSConfig: The parsed AWS configuration object.

    Raises:
        ValueError: If there is an issue with the AWS configuration format.
    """
    config = Config()
    aws_config_dict = config.get_object('aws') or {}

    try:
        # Isolate AWS configurations, ignoring compliance inline
        aws_config = AWSConfig.merge(aws_config_dict)
    except Exception as e:
        log.error(f"Invalid AWS configuration: {e}")
        raise

    return aws_config

def load_tenant_account_configs() -> Dict[str, TenantAccountConfig]:
    """
    Loads configurations for tenant accounts.

    Returns:
        Dict[str, TenantAccountConfig]: A dictionary containing configurations for each tenant account.
    """
    config = Config()
    aws_config_dict = config.get_object('aws') or {}
    tenant_accounts_list = aws_config_dict.get('landingzones', [])
    tenant_accounts = {}

    # TODO: use pulumi .apply method to ensure type Output objects are resolved
    for tenant in tenant_accounts_list:
        try:
            tenant_config = TenantAccountConfig(**tenant)
            tenant_accounts[tenant_config.name] = tenant_config
        except Exception as e:
            log.warn(f"Invalid tenant account configuration for '{tenant.get('name', 'unknown')}': {e}")
            continue

    return tenant_accounts
