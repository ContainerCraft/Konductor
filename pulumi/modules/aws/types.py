# pulumi/modules/aws/types.py

"""
This module defines the data classes for the AWS module.

The module defines the following data classes:

    - IAMUserConfig: Defines the IAM user configuration.
    - ControlTowerConfig: Defines the Control Tower configuration.
    - AWSConfig: Defines the AWS configuration.
    - TenantAccountConfig: Defines the tenant account configuration.
    - GlobalTags: Defines the global tags for resources.
"""

from dataclasses import dataclass, field, replace
from typing import List, Dict, Any

from pulumi import log

# Define a data class for IAM User configuration
@dataclass
class IAMUserConfig:
    name: str
    email: str
    groups: List[str] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)

# Define a data class for Control Tower configuration
@dataclass
class ControlTowerConfig:
    enabled: bool = False
    organizational_unit_name: str = "LandingZone"
    execution_role_name: str = "AWSControlTowerExecution"
    execution_role_arn: str = ""
    admin_role_name: str = "AWSControlTowerAdmin"
    admin_role_arn: str = ""
    audit_role_name: str = "AWSControlTowerAudit"
    audit_role_arn: str = ""
    log_archive_bucket: str = ""

# Define a data class for AWS configuration
@dataclass
class AWSConfig:
    profile: str = "main"
    region: str = "us-west-2"
    account_id: str = ""
    bucket: str = ""
    secret_access_key: str = ""
    access_key_id: str = ""
    control_tower: ControlTowerConfig = field(default_factory=ControlTowerConfig)
    iam_users: List[IAMUserConfig] = field(default_factory=list)
    landingzones: List['TenantAccountConfig'] = field(default_factory=list)
    enabled: bool = True

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> 'AWSConfig':
        """
        Merges user-provided configuration with the default AWS configuration.

        Args:
            user_config (Dict[str, Any]): The user-provided AWS configuration.

        Returns:
            AWSConfig: The merged AWSConfig instance.
        """
        default_config = AWSConfig()

        # Merge base fields
        for key, value in user_config.items():
            if hasattr(default_config, key):
                current_value = getattr(default_config, key)
                if isinstance(current_value, list) and isinstance(value, list):
                    # Merge lists
                    merged_value = current_value + value
                    setattr(default_config, key, merged_value)
                elif isinstance(current_value, dict) and isinstance(value, dict):
                    # Merge dicts (shallow merge)
                    merged_value = {**current_value, **value}
                    setattr(default_config, key, merged_value)
                else:
                    setattr(default_config, key, value)
            else:
                log.warn(f"Unknown Key '{key}' in AWSConfig")

        # Merge nested ControlTowerConfig
        if 'control_tower' in user_config:
            control_tower_dict = user_config['control_tower']
            default_control_tower_config = default_config.control_tower

            for key, value in control_tower_dict.items():
                if hasattr(default_control_tower_config, key):
                    setattr(default_control_tower_config, key, value)

            default_config.control_tower = default_control_tower_config

        # Merge IAM Users
        if 'iam_users' in user_config:
            user_configs = user_config['iam_users']
            merged_iam_users = []

            for user_dict in user_configs:
                user_config_obj = IAMUserConfig(
                    name=user_dict.get('name', ''),
                    email=user_dict.get('email', ''),
                    groups=user_dict.get('groups', []),
                    policies=user_dict.get('policies', [])
                )
                merged_iam_users.append(user_config_obj)

            default_config.iam_users = merged_iam_users

        # Merge LandingZones (TenantAccountConfigs)
        if 'landingzones' in user_config:
            landingzones_config = user_config['landingzones']
            merged_landingzones = []

            for zone_dict in landingzones_config:
                zone_config_obj = TenantAccountConfig(
                    name=zone_dict.get('name', ''),
                    email=zone_dict.get('email', ''),
                    administrators=zone_dict.get('administrators', []),
                    users=zone_dict.get('users', []),
                    features=zone_dict.get('features', []),
                    aws=zone_dict.get('aws', {}),
                    tags={tag['key']: tag['value'] for tag in zone_dict.get('tags', [])},
                )
                merged_landingzones.append(zone_config_obj)

            default_config.landingzones = merged_landingzones

        return default_config

# Define a data class for Tenant Account configuration
@dataclass
class TenantAccountConfig:
    name: str
    email: str
    administrators: List[str] = field(default_factory=list)
    users: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    aws: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

# Define a data class for global tags for resources (if applicable, otherwise ignore)
@dataclass
class GlobalTags:
    project: str = "konductor"
    managed_by: str = "NASA_SCIP_OPERATIONS"
