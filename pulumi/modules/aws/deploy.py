# pulumi/modules/aws/deploy.py

"""
AWS Module

This module defines the deployment logic for the AWS module.

Configurable resources supported include:
    - AWS Organization
    - Organizational Units, AWS Control Tower,
    - IAM
      - policy
      - roles
      - users
      - groups
      - permissions

The module extracts all configuration from the Pulumi configuration file (Pulumi.aws.yaml) and
enforces type checking and safe typing.

The module calls the following functions:
    - deploy: Defines the function to deploy the AWS module.
    - create_organization: Defines the function to create the AWS organization.
    - create_organizational_units: Defines the function to create the AWS organizational units.
    - create_iam_user: Defines the function to create the IAM user.
    - setup_control_tower: Defines the function to setup Control Tower.

The module uses the following functions:

    - load_aws_config: Defines the function to load the configuration for the AWS module.
    - load_tenant_account_configs: Defines the function to load the tenant account configuration.
    - create_organization: Defines the function to create the AWS organization.
    - create_organizational_units: Defines the function to create the AWS organizational units.
    - create_iam_user: Defines the function to create the IAM user.
    - setup_control_tower: Defines the function to setup Control Tower.

The module uses the following classes:

    - pulumi.Provider: Defines the Pulumi provider for AWS.
    - pulumi.ResourceOptions: Defines the Pulumi resource options.
    - pulumi.export: Defines the Pulumi export function.
    - pulumi_aws.Provider: Defines the Pulumi AWS provider.

The module uses the following resources:

    - aws.Provider: Defines the AWS provider.
    - aws.OrganizationsOrganization: Defines the AWS organization.
    - aws.OrganizationsOrganizationalUnit: Defines the AWS organizational unit.
    - aws.iam.User: Defines the AWS IAM user.
    - aws.iam.Group: Defines the AWS IAM group.
    - aws.iam.Policy: Defines the AWS IAM policy.
    - aws.iam.Role: Defines the AWS IAM role.
    - aws.iam.RolePolicyAttachment: Defines the AWS IAM role policy attachment.
    - aws.s3.Bucket: Defines the AWS S3 bucket.
    - aws.s3.BucketPolicy: Defines the AWS S3 bucket policy.
    - aws.organizations.Account: Defines the AWS organization account.

The module uses the following variables:

    - aws_config: Defines the AWS configuration.
    - tenant_account_configs: Defines the tenant account configuration.
    - provider: Defines the AWS provider.
    - organization: Defines the AWS organization.
    - ou_name: Defines the organizational unit name.
    - ou_resources: Defines the organizational unit resources.

The module returns the following:

    - pulumi.export: Exports the outputs of the Pulumi stack.

The module does the following:

    - Loads the configuration for the AWS module.
    - Loads the tenant account configuration.
    - Checks if AWS deployment is enabled.
    - Creates the AWS provider.
    - Creates the AWS organization.
    - Creates the AWS organizational units.
    - Creates the IAM user.
    - Sets up Control Tower.
"""

from typing import Dict, List

import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, export, Config, Output

# Import type-safe classes from aws/types.py
from .types import (
    AWSConfig,
    TenantAccountConfig,
    ControlTowerConfig,
    IAMUserConfig,
    GlobalTags,
)

# Import resource functions from aws/resources.py
from .resources import (
    load_aws_config,
    load_tenant_account_configs,
    create_organization,
    create_organizational_units,
    create_iam_users,
    create_tenant_accounts,
    deploy_tenant_resources,
    assume_role_in_tenant_account,
)

# ---------------------
# Main Deployment Function
# ---------------------

def deploy_aws_module():
    """
    Main function to deploy the AWS module.
    """
    # Load configurations
    aws_config = load_aws_config()
    tenant_configs = load_tenant_account_configs()

    # Check if AWS module deployment is enabled
    if not aws_config.enabled:
        pulumi.log.info("AWS module deployment is disabled.")
        return

    # Global tags
    global_tags = {
        "Project": "Pulumi-AWS-Infrastructure",
        "ManagedBy": "Pulumi",
    }

    # Create AWS provider
    aws_provider = aws.Provider(
        resource_name="aws_provider",
        profile=aws_config.profile,
        region=aws_config.region,
    )

    # Create AWS Organization
    organization = create_organization()

    # Create Organizational Units
    ou_resources = create_organizational_units(
        organization=organization,
        ou_names=[aws_config.control_tower.organizational_unit_name],
    )
    ou = ou_resources[aws_config.control_tower.organizational_unit_name]

    # Set up AWS Control Tower if enabled
    if aws_config.control_tower.enabled:
        setup_control_tower(aws_config.control_tower)

    # Create IAM users in the master account
    create_iam_users(aws_config.iam_users, global_tags)

    # Create Tenant Accounts
    tenant_accounts = create_tenant_accounts(
        organization=organization,
        ou=ou,
        tenant_configs=tenant_configs,
        tags=global_tags,
    )

    # For each tenant account, perform operations
    for tenant_account in tenant_accounts:
        # Assume role in tenant account
        tenant_provider = assume_role_in_tenant_account(
            tenant_account=tenant_account,
            role_name=aws_config.control_tower.execution_role_name,
            region=aws_config.region,
        )

        # Get tenant configuration
        tenant_config = tenant_configs[tenant_account.name]

        # Deploy resources in tenant account
        deploy_tenant_resources(
            tenant_provider=tenant_provider,
            tenant_account=tenant_account,
            tenant_config=tenant_config,
            global_tags=global_tags,
        )

    # Export outputs
    export("organization_arn", organization.arn)
    for ou_name, ou in ou_resources.items():
        export(f"organizational_unit_{ou_name}_id", ou.id)
    for tenant_account in tenant_accounts:
        export(f"{tenant_account.name}_account_id", tenant_account.id)

# Run the deployment function
deploy_aws_module()
