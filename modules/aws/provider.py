# ./modules/aws/provider.py
from typing import Optional, Dict, Any
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Config, log
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
            log.debug("Setting up AWS provider configuration")
            # Get AWS credentials and region with proper fallbacks
            pulumi_config = Config("aws")

            # Retrieve AWS region
            aws_region = (
                os.getenv("AWS_REGION") or
                pulumi_config.get("region") or
                self.config.region
            )
            if not aws_region:
                raise ValueError("AWS region is not specified.")

            # Retrieve AWS access key and secret access key
            access_key_id = os.getenv("AWS_ACCESS_KEY_ID") or pulumi_config.get_secret("access_key_id")
            secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY") or pulumi_config.get_secret("secret_access_key")

            # Retrieve AWS profile if access keys are not provided
            aws_profile = None
            if not access_key_id and not secret_access_key:
                aws_profile = os.getenv("AWS_PROFILE") or pulumi_config.get("profile") or self.config.profile
                if not aws_profile:
                    raise ValueError("AWS credentials not provided. Set access keys or profile.")

            self._region = aws_region

            # Initialize AWS provider with the appropriate authentication method
            provider_args = {
                "region": aws_region,
            }
            if access_key_id and secret_access_key:
                provider_args.update({
                    "access_key": access_key_id,
                    "secret_key": secret_access_key,
                })
                log.debug("Using AWS access key and secret key for authentication.")
            elif aws_profile:
                provider_args["profile"] = aws_profile
                log.debug(f"Using AWS profile '{aws_profile}' for authentication.")
            else:
                raise ValueError("AWS credentials not provided. Set access keys or profile.")

            log.debug(f"Created provider with args: {provider_args}")
            self._provider = aws.Provider("aws-provider", **provider_args)
            log.debug("AWS Provider instance created successfully")

            log.info(f"AWS Provider initialized in region: {aws_region}")

        except Exception as e:
            log.error(f"Failed to initialize AWS provider: {str(e)}")
            log.debug(f"Provider initialization failed with config: {self.config}")
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

            # Simplest possible version - no options merging
            return aws.get_caller_identity()

        except Exception as e:
            log.error(f"Failed to get caller identity: {str(e)}")
            raise

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
                "region": self._region
            }
        return self._tags
