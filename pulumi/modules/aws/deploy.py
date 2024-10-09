# pulumi/modules/aws/deploy.py

"""
AWS Module Deployment - Enhanced Compliance Metadata Propagation

This script initializes the AWS provider, retrieves the STS caller identity,
and ensures compliance metadata is propagated as tags.
"""

import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log
from typing import List, Dict

from .types import AWSConfig, TenantAccountConfig
from .config import initialize_aws_provider, generate_tags, load_tenant_account_configs
from .resources import (
    create_s3_bucket,
    create_organization,
    create_organizational_units,
    setup_control_tower,
    create_iam_users,
    create_tenant_accounts,
    deploy_tenant_resources,
    assume_role_in_tenant_account
)
from core.metadata import collect_git_info
from core.types import ComplianceConfig


def deploy_aws_module(config: AWSConfig, global_depends_on: List[pulumi.Resource]) -> pulumi.Resource:
    try:
        # Initialize AWS Provider
        aws_provider = initialize_aws_provider(config)

        # Generate global tags
        git_info = collect_git_info()
        compliance_config = ComplianceConfig.merge(config.dict())
        global_tags = generate_tags(config, compliance_config, git_info)

        # Create an S3 bucket for Ops data
        s3_bucket = create_s3_bucket(
            "konductor-bucket",
            global_tags,
            aws_provider,
            compliance_config,
        )
        pulumi.export("ops_data_bucket", s3_bucket.id)

        # Create AWS Organization
        organization = create_organization(aws_provider)

        # Setup Control Tower
        setup_control_tower(config.control_tower)

        # Create Organizational Units
        organizational_units = create_organizational_units(
            organization,
            ["Security", "Infrastructure", "Applications"],
            global_tags,
            aws_provider
        )

        # Ensure Outputs are properly used from previously created resources
        ou_applications = organizational_units.get("Applications")
        if ou_applications:
            tenant_accounts = create_tenant_accounts(
                organization,
                ou_applications,
                load_tenant_account_configs(),
                global_tags,
                aws_provider
            )

            # Deploy resources for each tenant
            tenant_account_configs = load_tenant_account_configs()

            for tenant_account in tenant_accounts:
                tenant_provider = assume_role_in_tenant_account(
                    tenant_account=tenant_account,
                    role_name="OrganizationAccountAccessRole",
                    region=config.region,
                    aws_provider=aws_provider
                )

                tenant_config = tenant_account_configs.get(tenant_account.name)
                if tenant_config:
                    deploy_tenant_resources(
                        tenant_provider,
                        tenant_account,
                        tenant_config,
                        global_tags
                    )

        pulumi.export("organization_id", organization.id)

        return organization, aws_provider, organization.id

    except Exception as e:
        log.error(f"Error deploying AWS module: {str(e)}")
        raise
