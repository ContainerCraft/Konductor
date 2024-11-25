# ./modules/aws/organization.py
"""AWS Organizations management and operations."""
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

if TYPE_CHECKING:
    from .provider import AWSProvider

class AWSOrganization:
    """
    Manages AWS Organizations resources and operations.
    """

    def __init__(self, provider: 'AWSProvider'):
        """
        Initialize AWS Organizations manager.

        Args:
            provider: AWSProvider instance for resource management
        """
        self.provider = provider
        self._organization: Optional[aws.organizations.Organization] = None
        self._org_data: Optional[aws.organizations.GetOrganizationResult] = None

    def get_or_create(self) -> Tuple[aws.organizations.Organization, aws.organizations.GetOrganizationResult]:
        """
        Retrieves existing AWS Organization or creates a new one.

        Returns:
            Tuple containing:
                - Organization resource
                - Organization data
        """
        try:
            log.debug("Attempting to get organization")
            # Try to get existing organization
            org_data = aws.organizations.get_organization(
                opts=pulumi.InvokeOptions(provider=self.provider.provider)
            )
            log.info(f"Found existing Organization with ID: {org_data.id}")

            # Create resource reference to existing organization
            organization = aws.organizations.Organization.get(
                "existing_organization",
                id=org_data.id,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                )
            )
            return organization, org_data

        except Exception as e:
            log.warn(f"No existing organization found, creating new: {str(e)}")

            # Create new organization with all features enabled
            organization = aws.organizations.Organization(
                "aws_organization",
                feature_set="ALL",
                aws_service_access_principals=[
                    "cloudtrail.amazonaws.com",
                    "config.amazonaws.com",
                    "sso.amazonaws.com"
                ],
                enabled_policy_types=[
                    "SERVICE_CONTROL_POLICY",
                    "TAG_POLICY"
                ],
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                )
            )

            # Get organization data after creation
            org_data = aws.organizations.get_organization(
                opts=pulumi.InvokeOptions(provider=self.provider.provider)
            )

            return organization, org_data

    def get_root_id(self, org_data: Dict[str, Any]) -> str:
        """Get the root ID from organization data."""
        if not org_data.get("roots"):
            raise ValueError("Organization roots not found in org data")
        return org_data["roots"][0]["id"]
