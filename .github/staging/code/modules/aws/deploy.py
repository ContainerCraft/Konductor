# pulumi/modules/aws/deploy.py

"""
AWS Module Deployment - Enhanced Compliance Metadata Propagation

This script initializes the AWS provider, retrieves the STS caller identity,
and ensures compliance metadata is propagated as tags.
"""
from typing import List, Dict, Tuple, Optional, Any, TYPE_CHECKING
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

from core.metadata import collect_git_info
from core.types import ComplianceConfig
from .types import AWSConfig, TenantAccountConfig
from .config import (
    initialize_aws_provider,
    generate_tags,
    load_tenant_account_configs
)
from .exceptions import ResourceCreationError
from .provider import AWSProvider
from .resources import (
    create_s3_bucket,
    create_organization,
    create_organizational_units,
    setup_control_tower,
    create_iam_users,
    create_tenant_accounts,
    deploy_tenant_resources,
    assume_role_in_tenant_account,
    get_or_create_organization,
    get_organization_root_id,
)
from .security import SecurityManager
from .networking import NetworkManager

if TYPE_CHECKING:
    from pulumi import Resource

MODULE_NAME = "aws"
MODULE_VERSION = "0.0.1"


def deploy_aws_module(
    config: AWSConfig,
    global_depends_on: List[pulumi.Resource]
) -> Tuple[str, pulumi.Resource, Dict[str, Any]]:
    """
    Deploys the AWS module resources.

    Args:
        config (AWSConfig): AWS configuration.
        global_depends_on (List[pulumi.Resource]): Global dependencies.

    Returns:
        Tuple[str, pulumi.Resource]: A tuple containing the module version and the main AWS resource deployed.

    TODO:
    - Enhance error handling with custom exception types
    - Add rollback mechanisms for failed deployments
    - Implement deployment status tracking
    - Add deployment metrics collection
    - Enhance logging with structured logging
    """
    try:
        # Initialize AWS Provider
        aws_provider = initialize_aws_provider(config)

        # Generate global tags and register transformations
        git_info = collect_git_info()
        compliance_config = config.compliance
        # Log compliance_config to verify its content
        pulumi.log.info(f"AWS Module Compliance Config: {compliance_config}")
        module_tags = generate_tags(config, compliance_config, git_info)

        # Create a basic S3 bucket
        s3_bucket = create_s3_bucket(
            "konductor-bucket",
            aws_provider,
        )

        # Get existing AWS Organization and organization data
        organization, organization_data = get_or_create_organization(aws_provider)

        # Get the root ID from the organization data
        root_id = get_organization_root_id(organization_data)

        # Create organizational units and tenant accounts if enabled
        build_organizational_infrastructure: bool = False
        if build_organizational_infrastructure:
            # Create Organizational Units
            organizational_units = create_organizational_units(
                organization,
                root_id,
                ["SecOps", "Infrastructure", "Applications"],
                aws_provider,
            )

            # Create Tenant Accounts under 'Applications' OU
            ou_applications = organizational_units.get("Applications")
            if ou_applications:
                tenant_configs = load_tenant_account_configs()
                tenant_accounts = create_tenant_accounts(
                    organization,
                    ou_applications,
                    tenant_configs,
                    aws_provider
                )

                # Deploy resources for each tenant
                for tenant_account in tenant_accounts:
                    tenant_provider = assume_role_in_tenant_account(
                        tenant_account=tenant_account,
                        role_name="OrganizationAccountAccessRole",
                        region=config.region,
                        aws_provider=aws_provider,
                    )

                    tenant_config = tenant_configs.get(tenant_account.name)
                    if tenant_config:
                        deploy_tenant_resources(
                            tenant_provider,
                            tenant_account,
                            tenant_config
                        )

        # Deploy EKS if enabled
        if config.eks and config.eks.enabled:
            eks_cluster = provider.eks.create_cluster(
                config.eks,
                vpc.id,
                [subnet.id for subnet in private_subnets],
                opts=ResourceOptions(
                    provider=provider.provider,
                    depends_on=[vpc, *private_subnets]
                )
            )
            module_outputs["eks_cluster"] = {
                "name": eks_cluster.name,
                "endpoint": eks_cluster.endpoint,
                "version": eks_cluster.version
            }

        # Return Dictionary of AWS Module Resources to global configuration dictionary
        module_outputs = {
            "ops_data_bucket": s3_bucket.id,
            "organization": organization.id,
            "organization_arn": organization.arn,
            "aws_module_tags": module_tags,
        }

        # Return the module version and the main resource
        return MODULE_VERSION, organization, module_outputs

    except Exception as e:
        pulumi.log.error(f"Error deploying AWS module: {str(e)}")
        raise
