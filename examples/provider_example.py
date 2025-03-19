#!/usr/bin/env python3
# examples/provider_example.py

"""Example script demonstrating the provider system."""

import logging
import sys

from src.core.providers.provider_registry import ProviderRegistry
from src.providers.aws.aws_provider import AWSProvider


def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("provider_example")


def main():
    """Run the provider example."""
    logger = setup_logging()
    logger.info("Starting provider example")

    # Create a provider registry
    provider_registry = ProviderRegistry()
    logger.info("Created provider registry")

    # Create and register an AWS provider
    aws_provider = AWSProvider("aws-provider")
    provider_registry.register_provider(aws_provider)
    logger.info(
        f"Registered AWS provider with {len(aws_provider.get_resource_types())} "
        "resource types"
    )

    # Show available resource types
    resource_types = provider_registry.get_resource_types()
    logger.info(f"Available resource types: {resource_types}")

    # Create an EC2 instance
    logger.info("Creating an EC2 instance")
    if ec2_provider := provider_registry.get_provider_for_resource_type(
        "aws.ec2.instance"
    ):
        ec2_instance = ec2_provider.create_resource(
            resource_type="aws.ec2.instance",
            name="example-instance",
            instance_type="t2.micro",
            ami_id="ami-12345678",
            security_groups=["default"],
            subnet_id="subnet-12345678"
        )
        instance_id = ec2_instance['id'] if ec2_instance else 'Failed'
        logger.info(f"Created EC2 instance: {instance_id}")
    else:
        logger.error("No provider found for EC2 instance resource type")

    # Create an S3 bucket
    logger.info("Creating an S3 bucket")
    if s3_provider := provider_registry.get_provider_for_resource_type(
        "aws.s3.bucket"
    ):
        s3_bucket = s3_provider.create_resource(
            resource_type="aws.s3.bucket",
            name="example-bucket",
            bucket_name="example-bucket-12345",
            versioning=True,
            public_access=False
        )
        logger.info(f"Created S3 bucket: {s3_bucket['id'] if s3_bucket else 'Failed'}")
    else:
        logger.error("No provider found for S3 bucket resource type")

    # List resources
    logger.info("Listing all resources")
    for provider_name, provider in provider_registry.get_providers().items():
        resources = provider.list_resources()
        logger.info(f"Provider '{provider_name}' has {len(resources)} resources:")
        for resource_id, resource in resources.items():
            logger.info(f"  - {resource_id}: {resource['type']} ({resource['name']})")

    logger.info("Provider example completed successfully")


if __name__ == "__main__":
    main()
