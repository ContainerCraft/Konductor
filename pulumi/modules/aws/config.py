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

from typing import List, Dict
import pulumi
from pulumi import Config
from .types import AWSConfig, TenantAccountConfig, ControlTowerConfig, IAMUserConfig

def load_aws_config() -> AWSConfig:
    """
    Loads the configuration for the AWS module.

    Returns:
        AWSConfig: The AWS configuration.

    Raises:
        pulumi.ConfigError: If the configuration is invalid.
    """
    config = Config()
    aws_config_dict = config.get_object('aws') or {}

    # Load Control Tower configuration
    control_tower_dict = aws_config_dict.get('control_tower') or {}
    control_tower_config = ControlTowerConfig(
        enabled=control_tower_dict.get('enabled', False),
        organizational_unit_name=control_tower_dict.get('organizational_unit_name', 'LandingZone'),
        execution_role_name=control_tower_dict.get('execution_role_name', 'AWSControlTowerExecution'),
        execution_role_arn=control_tower_dict.get('execution_role_arn'),
        admin_role_name=control_tower_dict.get('admin_role_name', 'AWSControlTowerAdmin'),
        admin_role_arn=control_tower_dict.get('admin_role_arn'),
        audit_role_name=control_tower_dict.get('audit_role_name', 'AWSControlTowerAudit'),
        audit_role_arn=control_tower_dict.get('audit_role_arn'),
        log_archive_bucket=control_tower_dict.get('log_archive_bucket')
    )

    # Load IAM users configuration
    iam_users_config = aws_config_dict.get('iam_users', [])
    iam_users = [
        IAMUserConfig(
            name=user.get('name'),
            email=user.get('email'),
            groups=user.get('groups', []),
            policies=user.get('policies', [])
        )
        for user in iam_users_config
    ]

    # Create AWSConfig instance with values from the nested 'aws' configuration
    aws_config = AWSConfig(
        profile=aws_config_dict.get('profile'),
        region=aws_config_dict.get('region'),
        account_id=aws_config_dict.get('account_id'),
        bucket=aws_config_dict.get('bucket'),
        secret_access_key=aws_config_dict.get('secret_access_key'),
        access_key_id=aws_config_dict.get('access_key_id'),
        control_tower=control_tower_config,
        iam_users=iam_users,
        enabled=aws_config_dict.get('enabled', True)
    )

    # Load Landing Zones (Tenant Accounts)
    landingzones_list = aws_config_dict.get('landingzones', [])
    landingzones = []
    for zone_dict in landingzones_list:
        zone_config_obj = TenantAccountConfig(
            name=zone_dict.get('name', ''),
            email=zone_dict.get('email', ''),
            administrators=zone_dict.get('administrators', []),
            users=zone_dict.get('users', []),
            features=zone_dict.get('features', []),
            aws=zone_dict.get('aws', {}),
            tags={tag['key']: tag['value'] for tag in zone_dict.get('tags', [])},
        )
        landingzones.append(zone_config_obj)
    aws_config.landingzones = landingzones

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
