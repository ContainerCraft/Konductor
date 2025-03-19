# src/core/config/credentials.py

"""Secure credential management for the IaC framework.

This module provides functionality for securely handling credentials from
environment variables and Pulumi's secure configuration storage. It ensures
that credentials are never exposed in logs and that proper precedence is
followed when loading credentials from multiple sources.
"""

import os
import logging
import pulumi
from typing import Dict, Any, Optional, List, Tuple


class CredentialManager:
    """Securely manages credentials for the IaC framework.

    This class handles loading credentials from environment variables and
    Pulumi's secure configuration storage, ensuring that credentials are
    handled securely and following the correct precedence rules.
    """

    # Mapping of provider types to relevant credential environment variables
    ENV_VAR_MAPPINGS = {
        "aws": {
            "AWS_ACCESS_KEY_ID": "access_key_id",
            "AWS_SECRET_ACCESS_KEY": "secret_access_key",
            "AWS_SESSION_TOKEN": "session_token"
        },
        "azure": {
            "AZURE_TENANT_ID": "tenant_id",
            "AZURE_SUBSCRIPTION_ID": "subscription_id",
            "AZURE_CLIENT_ID": "client_id",
            "AZURE_CLIENT_SECRET": "client_secret"
        },
        "kubernetes": {
            "KUBECONFIG": "kubeconfig_path",
            "KUBE_TOKEN": "token"
        }
    }

    def __init__(self, pulumi_config: Optional[pulumi.Config] = None,
                 logger: Optional[logging.Logger] = None):
        """Initialize the credential manager.

        Args:
            pulumi_config: Optional Pulumi config instance for accessing secure config.
            logger: Optional logger instance.
        """
        self.pulumi_config = pulumi_config or pulumi.Config()
        self.logger = logger or logging.getLogger("core.config.credentials")

    def get_credentials(self, provider_type: str,
                        provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Get credentials for a specific provider.

        Handles precedence between environment variables and Pulumi secure config.
        Environment variables take precedence over Pulumi secure config.

        Args:
            provider_type: Type of provider (e.g., 'aws', 'azure', 'kubernetes').
            provider_name: Optional name for the provider instance. Used for
                           loading provider-specific credentials.

        Returns:
            Dictionary containing credential values for the provider.
        """
        credentials: Dict[str, Any] = {}

        # Try to load credentials from Pulumi secure config first
        pulumi_creds = self._get_pulumi_credentials(provider_type, provider_name)
        credentials.update(pulumi_creds)

        # Environment variables override Pulumi secure config
        env_creds = self._get_env_credentials(provider_type)
        credentials.update(env_creds)

        # Log the credential keys that were found (never log values)
        cred_keys = list(credentials.keys())
        if cred_keys:
            self.logger.debug(
                f"Loaded credentials for {provider_type}: {', '.join(cred_keys)}"
            )
        else:
            self.logger.debug(f"No credentials found for {provider_type}")

        return credentials

    def _get_env_credentials(self, provider_type: str) -> Dict[str, Any]:
        """Load provider credentials from environment variables.

        Args:
            provider_type: Type of provider (e.g., 'aws', 'azure', 'kubernetes').

        Returns:
            Dictionary containing credential values from environment variables.
        """
        if provider_type not in self.ENV_VAR_MAPPINGS:
            self.logger.debug(f"No environment variable mappings for {provider_type}")
            return {}

        env_creds = {}
        for env_var, cred_key in self.ENV_VAR_MAPPINGS[provider_type].items():
            value = os.environ.get(env_var)
            if value:
                env_creds[cred_key] = value
                self.logger.debug(f"Loaded credential from environment: {cred_key}")

        return env_creds

    def _get_pulumi_credentials(self, provider_type: str,
                                provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Load provider credentials from Pulumi secure configuration.

        Args:
            provider_type: Type of provider (e.g., 'aws', 'azure', 'kubernetes').
            provider_name: Optional name for the provider instance.

        Returns:
            Dictionary containing credential values from Pulumi secure config.
        """
        prefix = f"{provider_type}"
        if provider_name:
            prefix = f"{prefix}.{provider_name}"

        # Try to get credentials as an object first
        try:
            creds_key = f"{prefix}.credentials"
            creds = self.pulumi_config.get_object(creds_key, {})
            if creds:
                self.logger.debug(f"Loaded credentials from Pulumi config: {creds_key}")
                return creds
        except Exception as e:
            self.logger.debug(f"Error loading credentials object: {str(e)}")

        # Fall back to individual credential keys
        # This is provider-specific and should be expanded for each provider
        pulumi_creds = {}

        # Try common credential keys for each provider type
        if provider_type == "aws":
            self._try_get_secure(pulumi_creds, prefix, "access_key_id")
            self._try_get_secure(pulumi_creds, prefix, "secret_access_key")
            self._try_get_secure(pulumi_creds, prefix, "session_token")
        elif provider_type == "azure":
            self._try_get_secure(pulumi_creds, prefix, "tenant_id")
            self._try_get_secure(pulumi_creds, prefix, "subscription_id")
            self._try_get_secure(pulumi_creds, prefix, "client_id")
            self._try_get_secure(pulumi_creds, prefix, "client_secret")
        elif provider_type == "kubernetes":
            self._try_get_secure(pulumi_creds, prefix, "token")
            # Non-sensitive config may be stored in regular config
            kubeconfig = self.pulumi_config.get(f"{prefix}.kubeconfig_path")
            if kubeconfig:
                pulumi_creds["kubeconfig_path"] = kubeconfig
                self.logger.debug(f"Loaded kubeconfig_path from Pulumi config")

        return pulumi_creds

    def _try_get_secure(self, creds_dict: Dict[str, Any], prefix: str, key: str) -> None:
        """Try to get a secure config value and add it to the credentials dict.

        Args:
            creds_dict: Dictionary to update with the credential if found
            prefix: Configuration prefix
            key: Credential key to look for
        """
        try:
            value = self.pulumi_config.get_secret(f"{prefix}.{key}")
            if value:
                creds_dict[key] = value
                self.logger.debug(f"Loaded secure credential: {key}")
        except Exception:
            # No need to log this - it's normal for credentials to be missing
            pass