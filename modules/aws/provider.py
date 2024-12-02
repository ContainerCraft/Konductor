# ./modules/aws/provider.py
from typing import Optional, Dict, Any
import pulumi
import pulumi_aws as aws
from pulumi import log
import os

from .types import AWSConfig


class AWSProvider:
    """Manages AWS provider initialization and configuration."""

    def __init__(self, config: AWSConfig):
        """
        Initialize AWS provider with configuration.

        Args:
            config: AWS configuration settings
        """
        log.debug("Initializing AWSProvider")
        self.config = config
        self._provider: Optional[aws.Provider] = None
        self._tags: Dict[str, str] = {}
        self._region: str = ""

        try:
            # Load Pulumi configuration
            pulumi_config = pulumi.Config()
            aws_config = pulumi_config.get_object("aws") or {}

            # Fetch AWS region from Pulumi config or AWSConfig
            aws_region = aws_config.get("region") or self.config.region or os.getenv("AWS_REGION") or "us-east-1"
            self._region = aws_region

            # Prepare AWS provider arguments
            provider_args = {"region": aws_region}

            # Fetch AWS credentials from Pulumi config
            aws_access_key_id = aws_config.get("access_key_id")
            aws_secret_access_key = aws_config.get("secret_access_key")

            # If not in Pulumi config, check environment variables
            if not aws_access_key_id or not aws_secret_access_key:
                aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
                aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
                if aws_access_key_id and aws_secret_access_key:
                    log.debug("Using AWS credentials from environment variables.")

            # If credentials are found, add them to provider args
            if aws_access_key_id and aws_secret_access_key:
                provider_args.update(
                    {
                        "access_key": aws_access_key_id,
                        "secret_key": aws_secret_access_key,
                    }
                )
                log.debug("Using AWS credentials from Pulumi configuration.")
            else:
                # If no credentials, check for profile in Pulumi config or environment
                aws_profile = aws_config.get("profile") or self.config.profile or os.getenv("AWS_PROFILE")
                if aws_profile:
                    provider_args["profile"] = aws_profile
                    log.debug(f"Using AWS profile: {aws_profile}")
                else:
                    log.debug("No AWS credentials or profile found. Using default credential methods.")

            # Create the AWS provider
            log.debug(f"Creating AWS provider with args: {provider_args}")
            self._provider = aws.Provider("aws_provider", **provider_args)
            log.info(f"AWS Provider initialized in region: {aws_region}")

        except Exception as e:
            log.error(f"Failed to initialize AWS provider: {str(e)}")
            raise

    @property
    def provider(self) -> aws.Provider:
        """
        Get the AWS provider instance.

        Returns:
            aws.Provider: Initialized AWS provider

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self._provider:
            raise RuntimeError("AWS Provider not initialized")
        return self._provider

    @property
    def region(self) -> str:
        """
        Get the AWS region.

        Returns:
            str: The configured AWS region
        """
        return self._region

    def get_caller_identity(self) -> aws.GetCallerIdentityResult:
        """
        Get AWS caller identity information.

        Returns:
            aws.GetCallerIdentityResult: Caller identity information

        Raises:
            Exception: If caller identity check fails
        """
        try:
            if not self._provider:
                raise RuntimeError("AWS Provider not initialized")

            # Always use the provider's InvokeOptions
            return aws.get_caller_identity(opts=pulumi.InvokeOptions(provider=self._provider))

        except Exception as e:
            log.error(f"Failed to get caller identity: {str(e)}")
            raise

    def sanitize_tag_value(self, value: str) -> str:
        """
        Sanitize AWS tag values to meet AWS requirements:
        - Must be Unicode strings 1-256 characters long
        - Cannot be empty strings
        - Must not have leading/trailing spaces
        """
        if not value:
            return "none"

        # Convert to string and trim
        sanitized = value.strip()

        # Replace invalid characters with dashes
        sanitized = "".join(c if c.isalnum() or c in "-_.:/=+@" else "-" for c in sanitized)

        # Truncate to 256 characters
        sanitized = sanitized[:256]

        # Ensure non-empty value
        return sanitized or "none"

    def sanitize_tags(self, tags: Dict[str, str]) -> Dict[str, str]:
        """Sanitize all tag values in a dictionary."""
        return {k: self.sanitize_tag_value(v) for k, v in tags.items() if k and v is not None}

    def get_tags(self) -> Dict[str, str]:
        """
        Get AWS resource tags.

        Returns:
            Dict[str, str]: Combined resource tags
        """
        if not self._tags:
            self._tags = {
                "managed-by": "konductor",
                "environment": self.config.profile or "default",
                "region": self._region,
            }
        # Sanitize tags before returning
        return self.sanitize_tags(self._tags)


def collect_module_metadata(global_metadata: Dict[str, Any], provider: AWSProvider) -> Dict[str, Any]:
    """Collect AWS-specific metadata."""
    try:
        caller_identity = aws.get_caller_identity(opts=pulumi.InvokeOptions(provider=provider.provider))

        aws_metadata = {
            "aws": {
                "aws_user_account_id": caller_identity.account_id,
                "aws_user_id": caller_identity.user_id,
                "aws_user_arn": caller_identity.arn,
            }
        }

        # Store in global metadata singleton
        from modules.core.metadata import MetadataSingleton

        MetadataSingleton().set_aws_metadata(aws_metadata["aws"])

        return aws_metadata

    except Exception as e:
        pulumi.log.warn(f"Could not collect AWS caller identity: {e}")
        return {"aws": {}}
