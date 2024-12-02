# ./modules/aws/deployment.py
from typing import Dict, Any, List
import pulumi
from pulumi import log
import pulumi_aws as aws
from pulumi import ResourceOptions

from modules.core.interfaces import ModuleInterface, ModuleDeploymentResult
from modules.core.types import InitializationConfig
from .provider import AWSProvider
from .types import AWSConfig
from modules.core.stack_outputs import collect_global_metadata, collect_module_metadata


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
            # Access init_config from the instance if necessary
            init_config = self.init_config

            # Ensure we have a valid config dictionary
            if not config:
                config = {}

            # Get AWS configuration from Pulumi config if not provided
            pulumi_config = pulumi.Config()
            aws_config_obj = pulumi_config.get_object("aws") or {}
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

            # Get Git info as dictionary
            git_info = init_config.git_info.model_dump()

            # Create example bucket with sanitized tags
            bucket_name = f"konductor-{init_config.stack_name}-{provider.region}"
            example_bucket = aws.s3.Bucket(
                bucket_name,
                tags=provider.sanitize_tags(
                    {
                        **provider.get_tags(),
                        "git:commit": git_info["commit_hash"],
                        "git:branch": git_info["branch_name"],
                        "git:remote": git_info["remote_url"],
                    }
                ),
                opts=pulumi.ResourceOptions(
                    provider=provider.provider,
                    protect=False,
                ),
            )

            # Collect metadata for resource tagging
            global_metadata = collect_global_metadata()
            aws_metadata = collect_module_metadata(
                global_metadata=global_metadata,
                modules_metadata={
                    "aws": {
                        "account_id": caller_identity.account_id,
                        "user_id": caller_identity.user_id,
                        "arn": caller_identity.arn,
                    }
                },
            )

            # Sanitize resource tags
            resource_tags = provider.sanitize_tags(
                {
                    "Project": aws_metadata["project_name"],
                    "Stack": aws_metadata["stack_name"],
                    "GitCommit": aws_metadata.get("commit_hash", ""),
                    "AWSAccountID": aws_metadata.get("aws", {}).get("account_id", ""),
                    "Compliance:Framework": "NIST",
                    "Compliance:Controls": "AC-2, AC-3",
                }
            )

            # Define AWS resources with sanitized tags
            s3_bucket = aws.s3.Bucket(
                "exampleBucket",
                bucket=aws_config.bucket,
                tags=resource_tags,
                opts=ResourceOptions(provider=provider.provider, protect=False),
            )

            # Export outputs
            pulumi.export("aws_s3_bucket_name", s3_bucket.id)

            # Collect AWS caller identity
            caller_identity = aws.get_caller_identity(opts=pulumi.InvokeOptions(provider=provider.provider))

            # Log success
            log.info(f"Successfully authenticated as: {caller_identity.arn}")

            # Collect AWS-specific metadata
            aws_metadata = {
                "aws_account_id": caller_identity.account_id,
                "aws_user_id": caller_identity.user_id,
                "aws_arn": caller_identity.arn,
            }

            # Collect resource identifiers
            provider_urn = str(provider.provider.urn)
            bucket_name = str(example_bucket.id)

            # Return deployment result without version
            return ModuleDeploymentResult(
                success=True,
                version="",  # Empty string since AWS module doesn't use versions
                resources=[provider_urn, bucket_name],  # Pass strings instead of objects
                metadata=aws_metadata,
            )

        except Exception as e:
            log.error(f"AWS deployment failed: {str(e)}")
            return ModuleDeploymentResult(
                success=False, version="", errors=[str(e)]  # Empty string since AWS module doesn't use versions
            )

    def get_dependencies(self) -> List[str]:
        """Get module dependencies."""
        return []
