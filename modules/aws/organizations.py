# pulumi/modules/aws/organization.py

"""AWS Organizations management and operations."""
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

if TYPE_CHECKING:
    from .types import TenantAccountConfig
    from .provider import AWSProvider
    from .resources import create_tenant_account, assume_role_in_tenant_account, deploy_tenant_resources

class AWSOrganization:
    """
    Manages AWS Organizations resources and operations.

    This class handles:
    - Organization creation and management
    - Organizational Unit (OU) operations
    - Account management
    - Control Tower integration
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

        Raises:
            Exception: If unable to retrieve or create organization
        """
        try:
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
        """
        Get the root ID from organization data.

        Args:
            org_data: Organization data dictionary

        Returns:
            str: Root ID of the organization
        """
        if not org_data.get("roots"):
            raise ValueError("Organization roots not found in org data")
        return org_data["roots"][0]["id"]

    def create_units(
        self,
        organization: aws.organizations.Organization,
        root_id: str,
        unit_names: List[str]
    ) -> Dict[str, aws.organizations.OrganizationalUnit]:
        """
        Creates Organizational Units under the organization root.

        Args:
            organization: The AWS Organization resource
            root_id: The root ID to create OUs under
            unit_names: List of OU names to create

        Returns:
            Dict[str, OrganizationalUnit]: Created OUs mapped by name

        Raises:
            ValueError: If root_id is invalid
        """
        if not root_id:
            raise ValueError("Root ID is required to create Organizational Units")

        organizational_units = {}

        for unit_name in unit_names:
            # Create OU with standard naming
            ou = aws.organizations.OrganizationalUnit(
                f"ou_{unit_name.lower()}",
                name=unit_name,
                parent_id=root_id,
                tags=self.provider.get_tags(),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=organization,
                    protect=True
                )
            )
            organizational_units[unit_name] = ou

            # Create default policies for the OU
            self._create_ou_policies(ou, unit_name)

        return organizational_units

    def _create_ou_policies(
        self,
        ou: aws.organizations.OrganizationalUnit,
        ou_name: str
    ) -> None:
        """
        Creates default policies for an Organizational Unit.

        Args:
            ou: The OU to create policies for
            ou_name: Name of the OU for policy naming
        """
        # Create Service Control Policy
        scp = aws.organizations.Policy(
            f"scp_{ou_name.lower()}",
            content=self._get_default_scp_content(ou_name),
            name=f"{ou_name}-BaselinePolicy",
            type="SERVICE_CONTROL_POLICY",
            tags=self.provider.get_tags(),
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=ou,
                protect=True
            )
        )

        # Attach policy to OU
        aws.organizations.PolicyAttachment(
            f"scp_attachment_{ou_name.lower()}",
            policy_id=scp.id,
            target_id=ou.id,
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=scp,
                protect=True
            )
        )

    def _get_default_scp_content(self, ou_name: str) -> str:
        """
        Gets default SCP content based on OU type.

        Args:
            ou_name: Name of the OU to determine policy content

        Returns:
            str: JSON policy content
        """
        if ou_name == "Security":
            return """{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "RequireIMDSv2",
                        "Effect": "Deny",
                        "Action": "ec2:RunInstances",
                        "Resource": "arn:aws:ec2:*:*:instance/*",
                        "Condition": {
                            "StringNotEquals": {
                                "ec2:MetadataHttpTokens": "required"
                            }
                        }
                    }
                ]
            }"""
        elif ou_name == "Workloads":
            return """{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "DenyUnencryptedVolumes",
                        "Effect": "Deny",
                        "Action": "ec2:CreateVolume",
                        "Resource": "*",
                        "Condition": {
                            "Bool": {
                                "aws:SecureTransport": "false"
                            }
                        }
                    }
                ]
            }"""
        else:
            return """{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "*",
                        "Resource": "*"
                    }
                ]
            }"""

    def create_account(
        self,
        name: str,
        email: str,
        parent_id: str,
        role_name: str = "OrganizationAccountAccessRole"
    ) -> aws.organizations.Account:
        """
        Creates a new AWS account in the organization.

        Args:
            name: Account name
            email: Account root email
            parent_id: Parent OU ID
            role_name: IAM role name for account access

        Returns:
            aws.organizations.Account: Created account resource
        """
        account = aws.organizations.Account(
            f"account_{name.lower()}",
            name=name,
            email=email,
            parent_id=parent_id,
            role_name=role_name,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(
                provider=self.provider.provider,
                protect=True
            )
        )

        # Wait for account to be created before returning
        account.id.apply(lambda id: log.info(f"Created account {name} with ID: {id}"))

        return account

    def move_account(
        self,
        account: aws.organizations.Account,
        source_parent: str,
        destination_parent: str
    ) -> None:
        """
        Moves an AWS account between organizational units.

        Args:
            account: Account to move
            source_parent: Source parent ID
            destination_parent: Destination parent ID
        """
        aws.organizations.AccountParent(
            f"move_{account.name}",
            account_id=account.id,
            parent_id=destination_parent,
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=account,
                protect=True,
                replace_on_changes=["parent_id"]
            )
        )

    def enable_aws_service_access(
        self,
        service_principal: str
    ) -> aws.organizations.DelegatedService:
        """
        Enables AWS service access in the organization.

        Args:
            service_principal: Service principal to enable (e.g. 'config.amazonaws.com')

        Returns:
            aws.organizations.DelegatedService: Service access resource
        """
        return aws.organizations.DelegatedService(
            f"service_access_{service_principal.split('.')[0]}",
            service_principal=service_principal,
            opts=ResourceOptions(
                provider=self.provider.provider,
                protect=True
            )
        )

    def enable_policy_type(
        self,
        policy_type: str
    ) -> aws.organizations.OrganizationalPolicyAttachment:
        """
        Enables a policy type in the organization.

        Args:
            policy_type: Type of policy to enable (e.g. 'SERVICE_CONTROL_POLICY')

        Returns:
            aws.organizations.OrganizationalPolicyAttachment: Policy type enablement
        """
        return aws.organizations.OrganizationalPolicyAttachment(
            f"enable_policy_{policy_type.lower()}",
            policy_type=policy_type,
            target_id=self._org_data.roots[0].id if self._org_data else None,
            opts=ResourceOptions(
                provider=self.provider.provider,
                protect=True
            )
        )

def deploy_tenant_infrastructure(
    tenant_config: TenantAccountConfig,
    parent_provider: aws.Provider,
    organization_id: str,
    depends_on: Optional[List[pulumi.Resource]] = None
) -> Dict[str, Any]:
    """
    Deploys infrastructure for a tenant account.

    Args:
        tenant_config: Tenant account configuration
        parent_provider: Parent AWS provider
        organization_id: AWS Organization ID
        depends_on: Optional resource dependencies

    Returns:
        Dict[str, Any]: Tenant infrastructure outputs

    TODO:
    - Implement tenant-specific compliance controls
    - Add tenant resource monitoring
    - Enhance tenant isolation mechanisms
    - Add tenant cost tracking
    - Implement tenant backup strategies
    """
    try:
        # Create tenant account
        tenant_account = create_tenant_account(
            tenant_config,
            parent_provider,
            organization_id,
            depends_on
        )

        # Assume role in tenant account
        tenant_provider = assume_role_in_tenant_account(
            tenant_account,
            "OrganizationAccountAccessRole",
            tenant_config.region,
            parent_provider
        )

        # Deploy tenant resources
        tenant_resources = deploy_tenant_resources(
            tenant_provider,
            tenant_account,
            tenant_config
        )

        return {
            "account_id": tenant_account.id,
            "account_arn": tenant_account.arn,
            "resources": tenant_resources
        }

    except Exception as e:
        pulumi.log.error(f"Error deploying tenant infrastructure: {str(e)}")
        raise
