# ./modules/aws/security.py
"""AWS Security Management Module"""
from typing import Dict, Any, Optional
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

from .provider import AWSProvider

class SecurityManager:
    """Manages AWS security resources and operations."""

    def __init__(self, provider: 'AWSProvider'):
        """Initialize Security manager."""
        self.provider = provider

    def deploy_security_controls(self) -> Dict[str, Any]:
        """Deploys security controls and returns outputs."""
        try:
            # Enable Security Hub
            security_hub = aws.securityhub.Account(
                "security-hub",
                enable_default_standards=True,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                )
            )

            # Enable GuardDuty
            guard_duty = aws.guardduty.Detector(
                "guard-duty",
                enable=True,
                finding_publishing_frequency="ONE_HOUR",
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                )
            )

            return {
                "security_hub_id": security_hub.id,
                "guard_duty_id": guard_duty.id
            }

        except Exception as e:
            log.error(f"Failed to deploy security controls: {str(e)}")
            raise
