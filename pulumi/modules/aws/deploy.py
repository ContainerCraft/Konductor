# pulumi/modules/aws/deploy.py

"""
AWS Module Deployment - Minimal Version for Provider Setup Verification

This script initializes the AWS provider and retrieves the STS caller identity
to verify the setup and credentials are correct.
"""

import os

import pulumi
import pulumi_aws as aws
from pulumi import Output, Resource, ResourceOptions, log

from .types import AWSConfig
from core.metadata import get_global_labels, get_global_annotations

MODULE_NAME = "aws"

def deploy_aws_module(
    config: AWSConfig,
    global_depends_on: list[pulumi.Resource],
) -> pulumi.Resource:
    """
    Deploys the AWS module and returns the primary AWS resource.

    Args:
        config (AWSConfig): The AWS module configuration object.
        global_depends_on (List[pulumi.Resource]): List of global dependencies.

    Returns:
        pulumi.Resource: The primary AWS resource (for now, just the STS caller identity).
    """
    # Check for environment variables and fallback to config values
    c = pulumi.Config("aws")
    pulumi.export("config", c)
    profile = os.getenv('AWS_PROFILE', c.get("profile"))
    access_key = os.getenv('AWS_ACCESS_KEY_ID', c.get("access_key_id"))
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', c.get("secret_access_key"))
    session_token = os.getenv('AWS_SESSION_TOKEN', None)

    # Initialize the AWS provider
    aws_provider = aws.Provider(
        "awsProvider",
        access_key=access_key,
        secret_key=secret_key,
        token=session_token,
        region=config.region,
        profile=profile,
    )

    # Export AWS Provider as a secret stack output for utilization by other dependent stacks
    aws_provider_secret = pulumi.Output.secret(aws_provider)
    pulumi.export("aws_provider", aws_provider_secret)

    # Retrieve global labels and annotations
    global_labels = get_global_labels()
    global_annotations = get_global_annotations()
    module_tags = {
        "iac_module_name": MODULE_NAME,
    }
    all_module_tags = {
        **global_labels,
        **global_annotations,
        **module_tags,
    }
    pulumi.export("aws_module_tags", all_module_tags)

    # Retrieve STS Caller Identity to verify the credentials
    sts_identity = aws.get_caller_identity(opts=pulumi.InvokeOptions(provider=aws_provider))
    all_module_tags["sts_identity"] = sts_identity.arn

    # Create an S3 bucket
    bucket = aws.s3.Bucket(
        "magic-testing-bucket",
        bucket="magic-testing-bucket",
        tags=all_module_tags,
        opts=pulumi.ResourceOptions(provider=aws_provider)
    )

    # Function to get organization details with error handling
    def get_organization():
        try:
            return aws.organizations.get_organization()
        except Exception as e:
            pulumi.log.warn(f"Failed to get existing organization: {e}")
            return None

    # Attempt to retrieve existing AWS Organization
    organization_details = get_organization()

    if organization_details:
        # Successfully fetched organization; export its ID
        pulumi.export("organization_lookup_id", organization_details.id)

        # Check if there are roots
        if organization_details.roots:
            # Fetch the root ID
            root_id = organization_details.roots[0].id

            # Create an Organizational Unit using the root_id as parent_id if desired
            create_organizational_units: bool = True
            if create_organizational_units:
                ou = aws.organizations.OrganizationalUnit(
                    "magic-ou",
                    name="magic-ou",
                    parent_id=root_id,
                    tags=all_module_tags,
                )
                pulumi.export("ou_id", ou.id)
            else:
                pulumi.log.warn("Organizational units creation is disabled")
        else:
            pulumi.log.warn("No roots found in the organization. Not creating Organizational Units.")
    else:
        pulumi.log.warn("The account is not part of an existing organization and create_organization flag is not set to True.")

    # Export the bucket name
    pulumi.export("bucket_name", bucket.id)

    # Log and export the caller identity to confirm it works
    log.info(f"Successfully retrieved STS caller identity: {sts_identity.arn}")
    pulumi.export("caller_identity", sts_identity.arn)

    # Add aws_provider to global dependencies to propagate through other resources if needed
    global_depends_on.append(aws_provider)

    return None, sts_identity
