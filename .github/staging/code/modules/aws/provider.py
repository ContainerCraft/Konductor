"""AWS Provider management and initialization."""
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
import os
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log
from pulumi_aws.cloudtrail import Trail
from pulumi_aws import Provider

from core.metadata import collect_git_info, generate_compliance_labels, generate_git_labels
from .types import AWSConfig, AWSManagers
from .exceptions import ComplianceError, ResourceCreationError
from .security import SecurityManager, setup_cloudtrail
from .networking import NetworkManager
from .organization import AWSOrganization
from .resources import ResourceManager
from .eks import EksManager

if TYPE_CHECKING:
    from pulumi import Resource
    from .organization import AWSOrganization
    from .resources import ResourceManager

class AWSProvider:
    """
    Manages AWS provider initialization and global configuration.

    This class handles:
    - Provider initialization and credentials
    - Global tag management
    - Resource deployment orchestration
    - Compliance metadata integration
    """

    def __init__(self, config: AWSConfig):
        """
        Initialize AWS provider with configuration.

        Args:
            config (AWSConfig): AWS configuration settings
        """
        self.config = config
        self._provider: Optional[aws.Provider] = None
        self._tags: Dict[str, str] = {}
        self._organization: Optional[AWSOrganization] = None
        self._resources: Optional[ResourceManager] = None
        self._eks: Optional[EksManager] = None

    @property
    def provider(self) -> aws.Provider:
        """Get or create the AWS provider instance."""
        if not self._provider:
            self._provider = self._initialize_provider()
        return self._provider

    @property
    def organization(self) -> AWSOrganization:
        """Get or create the AWS Organizations manager."""
        if not self._organization:
            self._organization = AWSOrganization(self)
        return self._organization

    @property
    def resources(self) -> ResourceManager:
        """Get or create the Resource manager."""
        if not self._resources:
            self._resources = ResourceManager(self)
        return self._resources

    @property
    def eks(self) -> EksManager:
        """Get or create the EKS manager."""
        if not self._eks:
            self._eks = EksManager(self)
        return self._eks

    def _initialize_provider(self) -> aws.Provider:
        """
        Initialize the AWS provider with credentials and region.

        Returns:
            aws.Provider: Initialized AWS provider
        """
        aws_config = pulumi.Config("aws")

        # Get credentials with fallback chain
        access_key = (
            os.getenv("AWS_ACCESS_KEY_ID") or
            aws_config.get("access_key_id") or
            None
        )
        secret_key = (
            os.getenv("AWS_SECRET_ACCESS_KEY") or
            aws_config.get("secret_access_key") or
            None
        )

        # Create provider with credentials and configuration
        return aws.Provider(
            "awsProvider",
            access_key=access_key,
            secret_key=secret_key,
            profile=self.config.profile,
            region=self.config.region,
            # Add default tags to all resources
            default_tags={"tags": self.get_tags()},
            opts=ResourceOptions(
                protect=True,  # Protect provider from accidental deletion
                delete_before_replace=False,
            ),
        )

    def get_tags(self) -> Dict[str, str]:
        """
        Get global AWS resource tags including compliance metadata.

        Returns:
            Dict[str, str]: Combined tags from compliance and git metadata
        """
        if not self._tags:
            # Get git metadata
            git_info = collect_git_info()

            # Generate compliance labels
            compliance_labels = generate_compliance_labels(self.config.compliance)
            git_labels = generate_git_labels(git_info)

            # Combine all tags
            self._tags = {
                **compliance_labels,
                **git_labels,
                "managed-by": "konductor",
                "environment": self.config.profile,
                "region": self.config.region,
                "account-id": self.config.account_id,
            }

            log.info(f"Generated AWS resource tags: {self._tags}")

        return self._tags

    def deploy(
        self,
        dependencies: Optional[List[pulumi.Resource]],
        managers: AWSManagers
    ) -> Tuple[str, pulumi.Resource, Dict[str, Any]]:
        """
        Deploys AWS infrastructure using provided managers.
        Pulumi automatically handles dependencies and validation.
        """
        try:
            # Initialize core infrastructure
            org_resource, org_data = managers["organization"].get_or_create()

            # Get organization root ID
            root_id = managers["organization"].get_root_id(org_data)

            # Deploy security controls - dependencies handled automatically
            security_outputs = managers["security"].deploy_security_controls()

            # Deploy networking - dependencies handled automatically
            network_outputs = managers["networking"].deploy_network_infrastructure()

            # Deploy resources - dependencies handled automatically
            resource_outputs = managers["resources"].deploy_resources()

            # Outputs are validated automatically by Pulumi
            outputs = {
                **security_outputs,
                **network_outputs,
                **resource_outputs,
                "organization_id": org_resource.id,
                "organization_arn": org_resource.arn,
                "root_id": root_id
            }

            return "1.0.0", org_resource, outputs

        except Exception as e:
            log.error(f"Deployment failed: {str(e)}")
            raise

    def validate_config(self) -> None:
        """
        Validate the AWS provider configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.account_id:
            raise ValueError("AWS account ID is required")

        if not self.config.region:
            raise ValueError("AWS region is required")

        if self.config.control_tower.enabled:
            if not self.config.control_tower.execution_role_arn:
                raise ValueError("Control Tower execution role ARN is required when enabled")

    def validate_compliance(
        self,
        resource: pulumi.Resource,
        compliance_config: Dict[str, Any]
    ) -> None:
        """Validates resource compliance with requirements."""
        try:
            # Validate NIST controls
            if "nist" in compliance_config:
                self._validate_nist_controls(resource, compliance_config["nist"])

            # Validate FISMA requirements
            if "fisma" in compliance_config:
                self._validate_fisma_requirements(resource, compliance_config["fisma"])

            # Validate custom controls
            if "custom" in compliance_config:
                self._validate_custom_controls(resource, compliance_config["custom"])

        except Exception as e:
            raise ComplianceError(f"Compliance validation failed: {str(e)}")

    def _validate_nist_controls(self, resource: pulumi.Resource, controls: Dict[str, Any]) -> None:
        """Validate NIST controls."""
        pass  # TODO: Implement NIST validation

    def _validate_fisma_requirements(self, resource: pulumi.Resource, requirements: Dict[str, Any]) -> None:
        """Validate FISMA requirements."""
        pass  # TODO: Implement FISMA validation

    def _validate_custom_controls(self, resource: pulumi.Resource, controls: Dict[str, Any]) -> None:
        """Validate custom controls."""
        pass  # TODO: Implement custom validation


def deploy_security_controls(
    config: AWSConfig,
    provider: aws.Provider,
    depends_on: Optional[List[pulumi.Resource]] = None
) -> Dict[str, Any]:
    """
    Deploys security controls and compliance mechanisms.

    Args:
        config: AWS configuration
        provider: AWS provider
        depends_on: Optional resource dependencies

    Returns:
        Dict[str, Any]: Security control outputs

    TODO:
    - Implement automated security assessments
    - Add security control validation
    - Enhance audit logging
    - Add automated remediation
    - Implement security metrics collection
    """
    try:
        # Enable AWS Security Hub
        security_hub = aws.securityhub.Account(
            "security-hub",
            enable_default_standards=True,
            opts=ResourceOptions(
                provider=provider,
                depends_on=depends_on,
                protect=True
            )
        )

        # Enable GuardDuty
        guard_duty = aws.guardduty.Detector(
            "guard-duty",
            enable=True,
            finding_publishing_frequency="ONE_HOUR",
            opts=ResourceOptions(
                provider=provider,
                depends_on=depends_on,
                protect=True
            )
        )

        # Configure CloudTrail
        cloud_trail = setup_cloudtrail(
            config,
            provider,
            depends_on
        )

        return {
            "security_hub_id": security_hub.id,
            "guard_duty_id": guard_duty.id,
            "cloud_trail_arn": cloud_trail.arn
        }

    except Exception as e:
        pulumi.log.error(f"Error deploying security controls: {str(e)}")
        raise
