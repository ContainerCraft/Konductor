# ./modules/aws/deployment.py
"""
AWS Module Deployment

This module implements the AWS module interface and provides the deployment logic for AWS resources.
"""

from typing import Dict, Any, List
import pulumi
from pulumi import log
import pulumi_aws as aws
from pulumi import ResourceOptions

from modules.core import (
    ModuleInterface,
    ModuleDeploymentResult,
    InitializationConfig,
    collect_global_metadata,
    collect_module_metadata,
)

from .provider import AWSProvider
from .types import AWSConfig
from .eks.deployment import EksManager
from modules.kubernetes import KubernetesProviderRegistry


class AwsModule(ModuleInterface):
    """AWS module implementation."""

    def __init__(self, init_config: InitializationConfig):
        self.name = "aws"
        self.init_config = init_config

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate AWS configuration."""
        try:
            if config is None:
                config = {}

            # Ensure minimum required fields
            config.setdefault("enabled", True)
            config.setdefault("region", "us-east-1")

            AWSConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy AWS infrastructure."""
        try:
            # Early return if AWS is disabled
            if not config.get("enabled", True):
                log.info("AWS module is disabled - skipping deployment")
                return ModuleDeploymentResult(
                )

            log.info("Starting AWS module deployment")

            # Access init_config from the instance if necessary
            init_config = self.init_config

            # Get compliance config from init_config
            compliance_config = init_config.compliance_config

            # Ensure we have a valid config dictionary
            if not config:
                config = {}

            # Get AWS configuration from Pulumi config if not provided
            pulumi_config = pulumi.Config("aws")
            aws_config_obj = pulumi_config.get_object("") or {}
            config = {**aws_config_obj, **config}

            # Parse and validate config
            aws_config = AWSConfig(**config)

            # Initialize provider
            provider = AWSProvider(aws_config)

            log.info(f"Attempting AWS authentication in region: {provider.region}")

            # Get caller identity to verify credentials
            caller_identity = provider.get_caller_identity()

            # Log success
            log.info(f"Successfully authenticated as: {caller_identity.arn}")
            log.info(f"AWS Account ID: {caller_identity.account_id}")

            # Initialize metadata dict
            aws_metadata = {}
            k8s_provider = None

            # Deploy EKS if enabled
            if aws_config.eks and aws_config.eks.enabled and aws_config.eks.clusters:
                log.info(f"Deploying {len(aws_config.eks.clusters)} EKS clusters")
                eks_manager = EksManager(provider)
                eks_resources = eks_manager.deploy_clusters(aws_config.eks)

                # Store results in metadata
                aws_metadata["eks_clusters"] = {}

                # Register each cluster's provider
                for cluster_name, resources in eks_resources.items():
                    aws_metadata["eks_clusters"][cluster_name] = {
                        "cluster_name": resources["cluster"].name,
                        "cluster_endpoint": resources["cluster"].endpoint,
                        "cluster_vpc_id": resources["vpc"].id,
                    }

                    if k8s_provider := resources.get("k8s_provider"):
                        provider_id = f"aws-eks-{cluster_name}"
                        # Get registry from kubernetes module
                        registry = KubernetesProviderRegistry()
                        registry.register_provider(
                            provider_id=provider_id,
                            provider=k8s_provider,
                            cluster_name=cluster_name,
                            platform="aws",
                            environment=resources.get("environment", "unknown"),
                            region=provider.region,
                            metadata={
                                "vpc_id": resources["vpc"].id,
                                "cluster_endpoint": resources["cluster"].endpoint,
                            }
                        )
                        log.info(f"Successfully registered k8s provider for cluster: {cluster_name}")
                    else:
                        log.warn(f"No k8s_provider available for cluster: {cluster_name}")

                # Export EKS outputs
                for name, resources in eks_resources.items():
                    pulumi.export(f"eks_cluster_{name}_name", resources["cluster"].name)
                    pulumi.export(f"eks_cluster_{name}_endpoint", resources["cluster"].endpoint)
                    pulumi.export(f"eks_cluster_{name}_vpc_id", resources["vpc"].id)

            # Get Git info as dictionary
            git_info = init_config.git_info.model_dump()

            # Collect metadata for resource tagging
            global_metadata = collect_global_metadata()

            # Update aws_metadata with caller identity info
            caller_identity = provider.get_caller_identity()
            aws_metadata.update({
                "account_id": caller_identity.account_id,
                "user_id": caller_identity.user_id,
                "arn": caller_identity.arn,
            })

            # Merge with global metadata
            combined_metadata = collect_module_metadata(
                global_metadata=global_metadata,
                modules_metadata={"aws": aws_metadata},
            )

            # Sanitize resource tags
            resource_tags = provider.sanitize_tags({
                "Project": combined_metadata["project_name"],
                "Stack": combined_metadata["stack_name"],
                "GitCommit": combined_metadata.get("commit_hash", ""),
                "AWSAccountID": aws_metadata["account_id"],
                "Compliance:Framework": "NIST",
                "Compliance:Controls": "AC-2, AC-3",
            })

            # Define AWS resources with sanitized tags
            bucket_name = f"konductor-{init_config.stack_name}-{provider.region}"
            s3_bucket = aws.s3.Bucket(
                bucket_name,
                bucket=aws_config.bucket,
                tags=resource_tags,
                opts=ResourceOptions(
                    provider=provider.provider,
                    protect=False,
                    parent=provider.provider
                ),
            )

            # Export outputs
            pulumi.export("aws_s3_bucket_name", s3_bucket.id)

            # Return deployment result
            return ModuleDeploymentResult(
                success=True,
                version="0.0.1",
                resources=[str(provider.provider.urn), str(s3_bucket.id)],
                metadata={
                    "compliance": init_config.compliance_config.model_dump(),
                    "aws_account_id": caller_identity.account_id,
                    "aws_user_id": caller_identity.user_id,
                    "aws_arn": caller_identity.arn,
                    "k8s_provider": k8s_provider if k8s_provider else None,
                    **aws_metadata,
                },
            )

        except Exception as e:
            log.error(f"AWS module deployment failed: {str(e)}")
            raise  # Let Pulumi handle the error

    def get_dependencies(self) -> List[str]:
        """Get module dependencies."""
        return []
