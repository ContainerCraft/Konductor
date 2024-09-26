# pulumi/modules/aws/types.py

"""
This module defines the data classes for the AWS module.

The module defines the following data classes:

    - IAMUserConfig: Defines the IAM user configuration.
    - ControlTowerConfig: Defines the Control Tower configuration.
    - AWSConfig: Defines the AWS configuration.
    - TenantAccountConfig: Defines the tenant account configuration.
    - AWSModuleConfig: Defines the AWS module configuration.
"""

from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class IAMUserConfig:
    name: str
    email: str
    groups: List[str] = field(default_factory=list)
    policies: List[str] = field(default_factory=list)

@dataclass
class ControlTowerConfig:
    enabled: bool
    organizational_unit_name: str
    execution_role_name: str
    execution_role_arn: str
    admin_role_name: str
    admin_role_arn: str
    audit_role_name: str
    audit_role_arn: str
    log_archive_bucket: str

@dataclass
class AWSConfig:
    profile: str
    region: str
    account_id: str
    bucket: str
    secret_access_key: str
    access_key_id: str
    control_tower: ControlTowerConfig
    iam_users: List[IAMUserConfig]
    enabled: bool

@dataclass
class TenantAccountConfig:
    name: str
    email: str
    administrators: List[str] = field(default_factory=list)
    users: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    aws: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class GlobalTags:
    project: str
    managed_by: str
