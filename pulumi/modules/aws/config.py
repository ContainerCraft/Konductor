# pulumi/modules/aws/config.py

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
from typing import Dict, Any, Optional
import pulumi
from pulumi import log, Config, ResourceTransformationResult, ResourceTransformationArgs
from pulumi_aws import Provider
from core.metadata import get_global_labels, generate_compliance_labels, generate_git_labels
from core.types import ComplianceConfig
from .types import AWSConfig, TenantAccountConfig
from .taggable import TAGGABLE_RESOURCES

# Constants
MODULE_NAME = "aws"
MODULE_VERSION = "0.0.1"

def initialize_aws_provider(config: AWSConfig) -> Provider:
    """
    Initializes the AWS provider with the supplied configuration.

    Args:
        config (AWSConfig): AWS configuration with provider details.

    Returns:
        Provider: An initialized AWS Provider for resource management.
    """
    aws_config = pulumi.Config("aws")
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID') or aws_config.get("access_key_id")
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or aws_config.get("secret_access_key")
    profile = os.getenv('AWS_PROFILE') or config.profile

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
    def global_transform(args: ResourceTransformationArgs) -> Optional[ResourceTransformationResult]:
        resource_type = args.type_

        # Check if the resource type is in the list of taggable resources
        if resource_type in TAGGABLE_RESOURCES:
            props = args.props.copy()
            opts = args.opts

            # Merge existing tags with global tags
            tags = props.get('tags') or {}
            tags.update(global_tags)
            props['tags'] = tags

            return ResourceTransformationResult(props, opts)
        else:
            # Do not modify resources that do not support tags
            return None

    pulumi.runtime.register_stack_transformation(global_transform)

# pulumi/modules/aws/config.py

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
    pulumi.export("aws_module_tags", aws_module_tags)

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
    aws_config_dict = config.get_object('aws') or {}
    compliance_config_dict = config.get_object('compliance') or {}

    # Include the compliance config into the aws_config_dict
    aws_config_dict['compliance'] = compliance_config_dict

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
    aws_config_dict = config.get_object('aws') or {}
    tenant_accounts_list = aws_config_dict.get('landingzones', [])
    tenant_accounts = {}

    for tenant in tenant_accounts_list:
        try:
            tenant_config = TenantAccountConfig(**tenant)
            tenant_accounts[tenant_config.name] = tenant_config
        except Exception as e:
            log.warn(f"Invalid tenant account configuration for '{tenant.get('name', 'unknown')}': {e}")

    return tenant_accounts
