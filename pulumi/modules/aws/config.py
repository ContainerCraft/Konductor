# pulumi/modules/aws/types.py

"""
AWS Module Configuration Loader.

This module defines functions to load and parse the AWS module configurations
using the Pydantic-based AWSConfig model.

The module defines the following functions:
    - load_config: Defines the function to load the configuration for the AWS module.
"""

from typing import Dict
import pulumi
from pulumi import Config, log
from .types import AWSConfig, TenantAccountConfig, ControlTowerConfig, IAMUserConfig


def load_aws_config() -> AWSConfig:
    """
    Loads the configuration for the AWS module.

    Returns:
        AWSConfig: The AWS configuration.
    """
    config = Config()
    aws_config_dict = config.get_object('aws') or {}

    try:
        aws_config = AWSConfig(**aws_config_dict)
    except Exception as e:
        log.error(f"Invalid AWS configuration: {e}")
        raise

    return aws_config


def load_tenant_account_configs() -> Dict[str, TenantAccountConfig]:
    """
    Loads tenant account configurations from Pulumi config.

    Returns:
        Dict[str, TenantAccountConfig]: A dictionary of tenant account configurations.
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
            continue

    return tenant_accounts
