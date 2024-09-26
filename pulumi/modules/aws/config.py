# pulumi/modules/aws/types.py

"""
This module defines the configuration for the AWS module.

The module defines the following functions:
    - load_config: Defines the function to load the configuration for the AWS module.
"""

from typing import List, Dict

import pulumi
from pulumi import ResourceOptions, export, Config, Output

from .types import (
    AWSConfig,
    TenantAccountConfig,
    ControlTowerConfig,
    IAMUserConfig
)

# ---------------------
# Configuration Loading
# ---------------------

def load_aws_config() -> AWSConfig:
    """
    Loads the configuration for the AWS module.

    Returns:
        AWSConfig: The AWS configuration.

    Raises:
        pulumi.ConfigError: If the configuration is invalid.
    """
    config = Config('aws')

    # Load Control Tower configuration
    control_tower_config = ControlTowerConfig(
        enabled=config.require_bool('control_tower.enabled'),
        organizational_unit_name=config.require('control_tower.organizational_unit_name'),
        execution_role_name=config.require('control_tower.execution_role_name'),
        execution_role_arn=config.require('control_tower.execution_role_arn'),
        admin_role_name=config.require('control_tower.admin_role_name'),
        admin_role_arn=config.require('control_tower.admin_role_arn'),
        audit_role_name=config.require('control_tower.audit_role_name'),
        audit_role_arn=config.require('control_tower.audit_role_arn'),
        log_archive_bucket=config.require('control_tower.log_archive_bucket'),
    )

    # Load IAM users configuration
    iam_users_config = config.get_object('iam.users') or []
    iam_users = [
        IAMUserConfig(
            name=user.get('name'),
            email=user.get('email'),
            groups=user.get('groups', []),
            policies=user.get('policies', []),
        )
        for user in iam_users_config
    ]

    # Create AWSConfig object
    aws_config = AWSConfig(
        profile=config.require('profile'),
        region=config.require('region'),
        account_id=config.require('account_id'),
        bucket=config.require('bucket'),
        secret_access_key=config.require('secret_access_key'),
        access_key_id=config.require('access_key_id'),
        control_tower=control_tower_config,
        iam_users=iam_users,
        enabled=True,
    )

    return aws_config

def load_tenant_account_configs() -> Dict[str, TenantAccountConfig]:
    """
    Loads tenant account configurations from Pulumi config.

    Returns:
        Dict[str, TenantAccountConfig]: A dictionary of tenant account configurations.
    """
    config = Config('landingzones')
    tenant_accounts_config = config.get_object('landingzones') or []
    tenant_accounts = {}

    for tenant in tenant_accounts_config:
        name = tenant.get('name')
        tenant_accounts[name] = TenantAccountConfig(
            name=name,
            email=tenant.get('email'),
            administrators=tenant.get('administrators', []),
            users=tenant.get('users', []),
            features=tenant.get('features', []),
            aws=tenant.get('aws', {}),
            tags={tag['key']: tag['value'] for tag in tenant.get('tags', [])},
        )

    return tenant_accounts
