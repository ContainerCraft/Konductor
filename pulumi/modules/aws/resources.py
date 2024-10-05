# pulumi/modules/aws/resources.py

"""
This module defines reusable resources for the AWS modules available as type safe functions.

The module defines the following resources:

    - create_organization: Defines the function to create an organization.
    - create_organizational_unit: Defines the function to create an organizational unit.
    - create_account: Defines the function to create an account.
    - create_control_tower: Defines the function to create an AWS Control Tower.
    - create_vpc: Defines the function to create a VPC.
    - create_subnet: Defines the function to create a subnet.
    - create_security_group: Defines the function to create a security group.
    - create_internet_gateway: Defines the function to create an internet gateway.
    - create_route_table: Defines the function to create a route table.
    - create_route: Defines the function to create a route.
    - create_subnet_route_table_association: Defines the function to create a subnet route table association.
    - create_security_group_rule: Defines the function to create a security group rule.
    - create_ec2_instance: Defines the function to create an EC2 instance.
    - todo: Add more resources as needed.
"""

import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, export, Config, Output
from typing import Dict, List

from .types import (
    ControlTowerConfig,
    IAMUserConfig,
    TenantAccountConfig,
)

# ---------------------
# AWS Organization Setup
# ---------------------

def create_organization() -> aws.organizations.Organization:
    """
    Creates an AWS Organization with all features enabled.

    Returns:
        aws.organizations.Organization: The AWS Organization resource.
    """
    organization = aws.organizations.Organization(
        resource_name="my_organization",
        feature_set="ALL",
        opts=ResourceOptions(protect=True),
    )
    return organization

def create_organizational_units(
    organization: aws.organizations.Organization,
    ou_names: List[str],
) -> Dict[str, aws.organizations.OrganizationalUnit]:
    """
    Creates Organizational Units (OUs) under the specified AWS Organization.

    Args:
        organization (aws.organizations.Organization): The AWS Organization resource.
        ou_names (List[str]): A list of OU names to create.

    Returns:
        Dict[str, aws.organizations.OrganizationalUnit]: A dictionary of OU resources.
    """
    ou_resources = {}
    root_id = organization.roots[0].id

    for ou_name in ou_names:
        ou = aws.organizations.OrganizationalUnit(
            resource_name=f"ou_{ou_name.lower()}",
            name=ou_name,
            parent_id=root_id,
            opts=ResourceOptions(parent=organization),
        )
        ou_resources[ou_name] = ou

    return ou_resources

# ---------------------
# AWS Control Tower Setup
# ---------------------

def setup_control_tower(control_tower_config: ControlTowerConfig) -> None:
    """
    Placeholder function to set up AWS Control Tower.

    Args:
        control_tower_config (ControlTowerConfig): The Control Tower configuration.
    """
    # Currently unable to declaratively configure AWS Control Tower via API or IaC tools.
    pulumi.log.info("AWS Control Tower setup is not fully automatable. Manual steps may be required.")

# ---------------------
# IAM Resources Setup
# ---------------------

def create_iam_users(iam_users: List[IAMUserConfig], tags: Dict[str, str]) -> None:
    """
    Creates IAM users, groups, and policies as specified in the configuration.

    Args:
        iam_users (List[IAMUserConfig]): A list of IAMUserConfig objects.
        tags (Dict[str, str]): A dictionary of tags to apply to resources.
    """
    for user_config in iam_users:
        # Create IAM User
        iam_user = aws.iam.User(
            resource_name=user_config.name,
            name=user_config.name,
            tags={**tags, "Email": user_config.email},
        )

        # Create IAM Groups and add user to groups
        for group_name in user_config.groups:
            iam_group = aws.iam.Group(
                resource_name=f"group_{group_name}",
                name=group_name,
                tags=tags,
            )
            aws.iam.UserGroupMembership(
                resource_name=f"{user_config.name}_{group_name}_membership",
                user=iam_user.name,
                groups=[iam_group.name],
            )

        # Attach policies to user
        for policy_arn in user_config.policies:
            aws.iam.UserPolicyAttachment(
                resource_name=f"{user_config.name}_{policy_arn.split('/')[-1]}",
                user=iam_user.name,
                policy_arn=policy_arn,
            )

# ---------------------
# Tenant Accounts Setup
# ---------------------

def create_tenant_accounts(
    organization: aws.organizations.Organization,
    ou: aws.organizations.OrganizationalUnit,
    tenant_configs: Dict[str, TenantAccountConfig],
    tags: Dict[str, str],
) -> List[aws.organizations.Account]:
    """
    Creates tenant accounts under the specified Organizational Unit.

    Args:
        organization (aws.organizations.Organization): The AWS Organization resource.
        ou (aws.organizations.OrganizationalUnit): The Organizational Unit resource.
        tenant_configs (Dict[str, TenantAccountConfig]): Tenant account configurations.
        tags (Dict[str, str]): Tags to apply to resources.

    Returns:
        List[aws.organizations.Account]: A list of AWS Account resources representing tenant accounts.
    """
    tenant_accounts = []

    for tenant_name, tenant_config in tenant_configs.items():
        tenant_account = aws.organizations.Account(
            resource_name=f"{tenant_name}_account",
            email=tenant_config.email,
            name=tenant_config.name,
            parent_id=ou.id,
            tags={**tags, **tenant_config.tags},
            opts=ResourceOptions(parent=ou),
        )
        tenant_accounts.append(tenant_account)

    return tenant_accounts

def assume_role_in_tenant_account(
    tenant_account: aws.organizations.Account,
    role_name: str,
    region: str,
) -> aws.Provider:
    """
    Assumes a role in the tenant account to perform operations.

    Args:
        tenant_account (aws.organizations.Account): The tenant AWS account.
        role_name (str): The name of the role to assume.
        region (str): The AWS region.

    Returns:
        aws.Provider: An AWS provider configured to operate in the tenant account.
    """
    role_arn = Output.all(tenant_account.id, tenant_account.arn).apply(
        lambda args: f"arn:aws:iam::{args[0]}:role/{role_name}"
    )
    tenant_provider = aws.Provider(
        resource_name=f"tenant_provider_{tenant_account.name}",
        assume_role=aws.ProviderAssumeRoleArgs(
            role_arn=role_arn,
            session_name="PulumiSession",
        ),
        region=region,
        opts=ResourceOptions(parent=tenant_account),
    )
    return tenant_provider

# ---------------------
# Workload Deployment in Tenant Accounts
# ---------------------

def deploy_tenant_resources(
    tenant_provider: aws.Provider,
    tenant_account: aws.organizations.Account,
    tenant_config: TenantAccountConfig,
    global_tags: Dict[str, str],
) -> None:
    """
    Deploys resources in the tenant account based on the configuration.

    Args:
        tenant_provider (aws.Provider): The AWS provider for the tenant account.
        tenant_account (aws.organizations.Account): The tenant AWS account.
        tenant_config (TenantAccountConfig): Configuration for the tenant account.
        global_tags (Dict[str, str]): Global tags to apply to resources.
    """
    # Implement resource deployment based on tenant_config.features
    # For example, deploy S3 bucket if 'bucket' feature is enabled
    if 'bucket' in tenant_config.features:
        bucket = aws.s3.Bucket(
            resource_name=f"{tenant_account.name}_bucket",
            bucket=f"{tenant_account.name}-bucket",
            acl="private",
            tags={**global_tags, **tenant_config.tags},
            opts=ResourceOptions(provider=tenant_provider, parent=tenant_account),
        )
        export(f"{tenant_account.name}_bucket_name", bucket.bucket)
