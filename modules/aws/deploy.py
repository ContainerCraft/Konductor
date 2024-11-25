# ./modules/aws/deploy.py
from typing import Dict, Any, List
import pulumi
from pulumi import log
import pulumi_aws as aws

from modules.core.interfaces import ModuleInterface, ModuleDeploymentResult
from modules.core.types import InitializationConfig
from .provider import AWSProvider
from .types import AWSConfig

class AWSModule(ModuleInterface):
    """AWS module implementation."""

    def __init__(self):
        self.name = "aws"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate AWS configuration."""
        try:
            AWSConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def pre_deploy_check(self) -> List[str]:
        """Perform pre-deployment checks."""
        return []

    def post_deploy_validation(self, result: ModuleDeploymentResult) -> List[str]:
        """Validate deployment results."""
        return []

    def deploy(self, config: Dict[str, Any], init_config: InitializationConfig) -> ModuleDeploymentResult:
        """Deploy AWS infrastructure."""
        try:
            # Parse and validate config
            aws_config = AWSConfig(**config)

            # Initialize provider
            provider = AWSProvider(aws_config)

            # Log provider region
            log.info(f"Attempting AWS authentication in region: {provider.region}")

            try:
                # Get caller identity to verify credentials
                caller_identity = provider.get_caller_identity()

                # Log success
                log.info(f"Successfully authenticated as: {caller_identity.arn}")
                log.info(f"AWS Account ID: {caller_identity.account_id}")

                # Create example bucket to verify provider works
                bucket_name = f"konductor-{init_config.stack_name}-{provider.region}"
                example_bucket = aws.s3.Bucket(bucket_name,
                    tags=provider.get_tags(),
                    opts=pulumi.ResourceOptions(
                        provider=provider.provider,
                        protect=False  # Don't protect example bucket
                    )
                )

                return ModuleDeploymentResult(
                    success=True,
                    version="1.0.0",
                    resources=[provider.provider, example_bucket],
                    metadata={
                        "caller_identity": {
                            "account_id": caller_identity.account_id,
                            "user_id": caller_identity.user_id,
                            "arn": caller_identity.arn
                        },
                        "bucket_name": example_bucket.bucket
                    }
                )

            except Exception as e:
                log.error(f"Failed to verify AWS provider: {str(e)}")
                raise

        except Exception as e:
            log.error(f"AWS deployment failed: {str(e)}")
            return ModuleDeploymentResult(
                success=False,
                version="1.0.0",
                errors=[str(e)]
            )

    def get_dependencies(self) -> List[str]:
        """Get module dependencies."""
        return []
