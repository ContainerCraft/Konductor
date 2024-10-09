# pulumi/modules/aws/resources.py

"""
This module defines reusable resources for the AWS modules available as type-safe functions.
The module defines the following resources:

    - create_organization: Defines the function to create an organization.
    - create_organizational_unit: Defines the function to create an organizational unit.
    - create_account: Defines the function to create an account.
    - create_control_tower: Defines the function to create an AWS Control Tower.
    - create_vpc: Defines the function to create a VPC.
    - create_subnet: Defines the function to create a subnet.
    - create_security_group: Defines the function to create a security group.
    - create_internet_gateway: Defines the function to create an internet gateway.
    - create_route_table: Defines the function to create a route table.
    - create_route: Defines the function to create a route.
    - create_subnet_route_table_association: Defines the function to create a subnet route table association.
    - create_security_group_rule: Defines the function to create a security group rule.
    - create_ec2_instance: Defines the function to create an EC2 instance.
    - todo: Add more resources as needed.
"""

from typing import Dict, List, Any, Tuple, Optional
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log
from .types import (
    ControlTowerConfig,
    IAMUserConfig,
    TenantAccountConfig,
    AWSConfig,
    GlobalTags,
)
from core.metadata import set_global_labels, set_global_annotations, generate_compliance_labels
from core.utils import set_resource_metadata

def fetch_sts_identity(aws_provider: aws.Provider) -> pulumi.Output[Dict[str, str]]:
    try:
        identity = aws.get_caller_identity(opts=pulumi.InvokeOptions(provider=aws_provider))

        # Map the output to a dictionary with explicit keys
        return pulumi.Output.from_input({
            "account_id": identity.account_id,
            "arn": identity.arn,
            "id": identity.id,
            "user_id": identity.user_id
        })
    except Exception as e:
        log.error(f"Error fetching STS Caller Identity: {str(e)}")
        raise

def create_s3_bucket(
        bucket_name: str,
        aws_provider: aws.Provider,
    ) -> aws.s3.Bucket:
    """
    Creates an S3 Bucket with the specified tags.

    Args:
        bucket_name (str): The name of the bucket.
        tags (dict): The tags to apply to the bucket.
        provider (aws.Provider): The AWS Provider.
        compliance_config (dict): The compliance configuration.

    Returns:
        aws.s3.Bucket: The created S3 bucket.
    """
    # Compliance labels now part of global transformations; ensure bucket tags are included.
    bucket = aws.s3.Bucket(
        bucket_name,
        opts=ResourceOptions(provider=aws_provider)
    )

    return bucket

def get_organization_details(provider: aws.Provider):
    try:
        return aws.organizations.get_organization(opts=pulumi.InvokeOptions(provider=aws_provider))
    except Exception as e:
        log.warn(f"Failed to get existing organization: {str(e)}")
    return None

def setup_organization_units(org_details, config: AWSConfig, tags: dict, aws_provider: aws.Provider):
    if org_details.roots:
        root_id = org_details.roots[0].id
        if config.control_tower.enabled:
            ou = aws.organizations.OrganizationalUnit(
                "example-ou",
                name="example-ou",
                parent_id=root_id,
                opts=pulumi.ResourceOptions(provider=aws_provider)
            )
            pulumi.export("ou_id", ou.id)
    else:
        log.warn("No roots found in the organization.")

def create_organization(aws_provider: aws.Provider) -> aws.organizations.Organization:
    """
    Creates an AWS Organization with all features enabled.

    Args:
        aws_provider (aws.Provider): The AWS provider.

    Returns:
        aws.organizations.Organization: The AWS Organization resource.
    """
    try:
        organization = aws.organizations.Organization(
            resource_name="konductor-scip-dev",
            feature_set="ALL",
            opts=ResourceOptions(provider=aws_provider),
        )

        # Export the organization ID
        pulumi.export("organization_id", organization.id)

        # Use .apply to log the organization ID
        organization.id.apply(lambda org_id: log.info(f"Organization created with ID: {org_id}"))

        return organization

    except Exception as e:
        log.error(f"Failed to create organization: {str(e)}")
        raise

def get_organization_root_id(organization_data: aws.organizations.GetOrganizationResult) -> str:
    """
    Retrieves the root ID of the AWS Organization from the organization data.

    Args:
        organization_data: The organization data obtained from get_organization.

    Returns:
        str: The root ID.
    """
    try:
        # Get the roots from the organization data
        if organization_data.roots:
            root = organization_data.roots[0]
            root_id = root.id
            log.info(f"Organization Root ID: {root_id}")
            return root_id
        else:
            raise Exception("No roots found in the organization")
    except Exception as e:
        log.error(f"Error fetching organization roots: {str(e)}")
        raise

def get_or_create_organization(
        aws_provider: aws.Provider,
    ) -> Tuple[aws.organizations.Organization, aws.organizations.GetOrganizationResult]:
    """
    Retrieves the existing AWS Organization or creates a new one if it doesn't exist.

    Returns:
        Tuple[aws.organizations.Organization, aws.organizations.GetOrganizationResult]: The AWS Organization resource and the organization data.
    """
    try:
        # Get existing organization data
        organization_data = aws.organizations.get_organization(
            opts=pulumi.InvokeOptions(provider=aws_provider)
        )
        log.info(f"Found existing Organization with ID: {organization_data.id}")

        # Create an Organization resource referencing the existing organization
        organization = aws.organizations.Organization.get(
            resource_name="existing_organization",
            id=organization_data.id,
            opts=pulumi.ResourceOptions(provider=aws_provider)
        )
        return organization, organization_data

    except Exception as e:
        log.warn(f"No existing organization found, creating a new one: {str(e)}")
        # If you have permissions to create an organization then we can uncomment the following to create one
        # organization = create_organization(aws_provider)
        # return organization
        raise Exception("Unable to retrieve or create the AWS Organization")

def create_organizational_units(
    organization: aws.organizations.Organization,
    root_id: str,
    ou_names: List[str],
    aws_provider: aws.Provider
) -> Dict[str, aws.organizations.OrganizationalUnit]:
    """
    Creates Organizational Units (OUs) under the specified AWS Organization.

    Args:
        organization: The AWS Organization resource.
        root_id: The root ID of the organization.
        ou_names: List of OU names to create.
        aws_provider: The AWS provider.

    Returns:
        Dict[str, aws.organizations.OrganizationalUnit]: Created OUs.
    """
    ou_map = {}

    if root_id:
        for ou_name in ou_names:
            ou = aws.organizations.OrganizationalUnit(
                resource_name=f"ou_{ou_name.lower()}",
                name=ou_name,
                parent_id=root_id,
                opts=ResourceOptions(provider=aws_provider, parent=organization)
            )
            ou_map[ou_name] = ou
    else:
        log.warn("Root ID is not available; cannot create Organizational Units.")

    return ou_map

def setup_control_tower(control_tower_config: ControlTowerConfig) -> None:
    """
    Sets up AWS Control Tower based on the provided configuration.

    Args:
        control_tower_config (ControlTowerConfig): The Control Tower configuration.
    """
    if control_tower_config.enabled:
        # Placeholder for Control Tower setup logic
        # AWS Control Tower does not currently support full automation via API/IaC
        log.info("AWS Control Tower setup is enabled. Manual configuration may be required.")
    else:
        log.info("AWS Control Tower setup is disabled.")

def create_iam_users(
        iam_users: List[IAMUserConfig],
        tags: Dict[str, str],
        aws_provider: aws.Provider
    ) -> None:
    """
    Creates IAM users and associates them with groups and policies.

    Args:
        iam_users (List[IAMUserConfig]): A list of IAMUserConfig objects.
        tags (Dict[str, str]): The tags to apply to the IAM resources.
    """
    for user_config in iam_users:
        iam_user = aws.iam.User(
            resource_name=user_config.name,
            name=user_config.name,
            opts=pulumi.ResourceOptions(
                provider=aws_provider,
            )
        )

        for group_name in user_config.groups:
            iam_group = aws.iam.Group(
                resource_name=f"group_{group_name}",
                name=group_name,
                opts=pulumi.ResourceOptions(
                    provider=aws_provider,
                )
            )
            aws.iam.UserGroupMembership(
                resource_name=f"{user_config.name}_{group_name}_membership",
                user=iam_user.name,
                groups=[iam_group.name],
                opts=pulumi.ResourceOptions(
                    provider=aws_provider,
                )
            )

        for policy_arn in user_config.policies:
            aws.iam.UserPolicyAttachment(
                resource_name=f"{user_config.name}_{policy_arn.split('/')[-1]}",
                user=iam_user.name,
                policy_arn=policy_arn,
                opts=pulumi.ResourceOptions(
                    provider=aws_provider,
                )
            )

def create_tenant_accounts(
    organization: aws.organizations.Organization,
    ou: aws.organizations.OrganizationalUnit,
    tenant_configs: Dict[str, TenantAccountConfig],
    aws_provider: aws.Provider,
) -> List[aws.organizations.Account]:
    """
    Creates tenant accounts under the specified Organizational Unit.

    Args:
        organization: The AWS Organization resource.
        ou: The Organizational Unit resource.
        tenant_configs: Tenant account configurations.
        aws_provider: The AWS provider.

    Returns:
        List[aws.organizations.Account]: Tenant account resources.
    """
    tenant_accounts = []
    ou_id = ou.id if ou else None

    if ou_id:
        for tenant_name, tenant_config in tenant_configs.items():
            tenant_account = aws.organizations.Account(
                resource_name=f"{tenant_name}_account",
                email=tenant_config.email,
                name=tenant_config.name,
                parent_id=ou_id,
                opts=ResourceOptions(provider=aws_provider, parent=organization),
            )
            tenant_accounts.append(tenant_account)
    else:
        log.warn("Organizational Unit ID not found.")

    return tenant_accounts

def assume_role_in_tenant_account(
    tenant_account: aws.organizations.Account,
    role_name: str,
    region: str,
    aws_provider: aws.Provider
) -> aws.Provider:
    """
    Assumes a role in the tenant account to perform operations.

    Args:
        tenant_account: The tenant AWS account.
        role_name: The name of the role to assume.
        region: The AWS region.
        aws_provider: The AWS provider.

    Returns:
        aws.Provider: AWS provider configured for the tenant account.
    """
    return tenant_account.id.apply(lambda account_id:
        aws.Provider(
            f"tenant_provider_{account_id}",
            assume_role=aws.ProviderAssumeRoleArgs(
                role_arn=f"arn:aws:iam::{account_id}:role/{role_name}",
                session_name="PulumiSession",
            ),
            region=region,
        )
    )

def deploy_tenant_resources(
    tenant_provider: aws.Provider,
    tenant_account: aws.organizations.Account,
    tenant_config: TenantAccountConfig
) -> None:
    """
    Deploys resources in the tenant account based on the configuration.

    Args:
        tenant_provider: The AWS provider for the tenant account.
        tenant_account: The tenant AWS account.
        tenant_config: Configuration for the tenant account.
    """
    if not tenant_config:
        log.warn(f"Configuration for tenant account '{tenant_account.name}' is missing.")
        return

    if 'bucket' in tenant_config.features:
        bucket = aws.s3.Bucket(
            resource_name=f"{tenant_account.name}_bucket",
            bucket=tenant_account.name.apply(lambda x: f"{x}-bucket"),
            acl="private",
            opts=ResourceOptions(provider=tenant_provider, parent=tenant_account),
        )
        pulumi.export(f"{tenant_account.name}_bucket_name", bucket.bucket)

    if 'ec2' in tenant_config.features:
        ec2_instance = aws.ec2.Instance(
            resource_name=f"{tenant_account.name}_instance",
            ami="ami-0c94855ba95c71c99",  # Example AMI ID
            instance_type="t2.micro",
            opts=ResourceOptions(provider=tenant_provider, parent=tenant_account),
        )
        pulumi.export(f"{tenant_account.name}_instance_id", ec2_instance.id)

def create_vpc(
    vpc_name: str,
    cidr_block: str,
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.Vpc:
    """
    Creates a VPC with the specified configuration.

    Args:
        vpc_name (str): The name of the VPC.
        cidr_block (str): The CIDR block for the VPC.
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.Vpc: The created VPC resource.
    """
    if opts is None:
        opts = ResourceOptions()
    vpc = aws.ec2.Vpc(
        resource_name=vpc_name,
        cidr_block=cidr_block,
        enable_dns_hostnames=True,
        enable_dns_support=True,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return vpc

def create_subnet(
    subnet_name: str,
    cidr_block: str,
    vpc_id: str,
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.Subnet:
    """
    Creates a subnet within the specified VPC.

    Args:
        subnet_name (str): The name of the subnet.
        cidr_block (str): The CIDR block for the subnet.
        vpc_id (str): The ID of the VPC.
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.Subnet: The created subnet resource.
    """
    if opts is None:
        opts = ResourceOptions()
    subnet = aws.ec2.Subnet(
        resource_name=subnet_name,
        cidr_block=cidr_block,
        vpc_id=vpc_id,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return subnet

def create_security_group(
    sg_name: str,
    vpc_id: str,
    aws_provider: aws.Provider,
    description: str = "Default security group",
    opts: ResourceOptions = None,
) -> aws.ec2.SecurityGroup:
    """
    Creates a security group within the specified VPC.

    Args:
        sg_name (str): The name of the security group.
        vpc_id (str): The ID of the VPC.
        provider (aws.Provider): The AWS provider to use.
        description (str, optional): Description of the security group.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.SecurityGroup: The created security group resource.
    """
    if opts is None:
        opts = ResourceOptions()
    sg = aws.ec2.SecurityGroup(
        resource_name=sg_name,
        name=sg_name,
        description=description,
        vpc_id=vpc_id,
        ingress=[
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=22,
                to_port=22,
                cidr_blocks=["0.0.0.0/0"],
            ),
            aws.ec2.SecurityGroupIngressArgs(
                protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
        egress=[
            aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            ),
        ],
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return sg

def create_internet_gateway(
    igw_name: str,
    vpc_id: str,
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.InternetGateway:
    """
    Creates an Internet Gateway and attaches it to the specified VPC.

    Args:
        igw_name (str): The name of the Internet Gateway.
        vpc_id (str): The ID of the VPC.
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.InternetGateway: The created Internet Gateway resource.
    """
    if opts is None:
        opts = ResourceOptions()
    igw = aws.ec2.InternetGateway(
        resource_name=igw_name,
        vpc_id=vpc_id,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return igw

def create_route_table(
    rt_name: str,
    vpc_id: str,
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.RouteTable:
    """
    Creates a route table within the specified VPC.

    Args:
        rt_name (str): The name of the route table.
        vpc_id (str): The ID of the VPC.
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.RouteTable: The created route table resource.
    """
    if opts is None:
        opts = ResourceOptions()
    rt = aws.ec2.RouteTable(
        resource_name=rt_name,
        vpc_id=vpc_id,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return rt

def create_route(
    route_name: str,
    route_table_id: str,
    destination_cidr_block: str,
    gateway_id: str,
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.Route:
    """
    Creates a route in the specified route table.

    Args:
        route_name (str): The name of the route.
        route_table_id (str): The ID of the route table.
        destination_cidr_block (str): The destination CIDR block.
        gateway_id (str): The gateway ID (e.g., Internet Gateway ID).
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.Route: The created route resource.
    """
    if opts is None:
        opts = ResourceOptions()
    route = aws.ec2.Route(
        resource_name=route_name,
        route_table_id=route_table_id,
        destination_cidr_block=destination_cidr_block,
        gateway_id=gateway_id,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return route

def create_subnet_route_table_association(
    association_name: str,
    subnet_id: str,
    route_table_id: str,
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.RouteTableAssociation:
    """
    Associates a subnet with a route table.

    Args:
        association_name (str): The name of the association.
        subnet_id (str): The ID of the subnet.
        route_table_id (str): The ID of the route table.
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.RouteTableAssociation: The created association resource.
    """
    if opts is None:
        opts = ResourceOptions()
    association = aws.ec2.RouteTableAssociation(
        resource_name=association_name,
        subnet_id=subnet_id,
        route_table_id=route_table_id,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return association

def create_security_group_rule(
    rule_name: str,
    security_group_id: str,
    type: str,  # 'ingress' or 'egress'
    protocol: str,
    from_port: int,
    to_port: int,
    cidr_blocks: List[str],
    aws_provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.SecurityGroupRule:
    """
    Creates a security group rule.

    Args:
        rule_name (str): The name of the rule.
        security_group_id (str): The ID of the security group.
        type (str): The type of rule ('ingress' or 'egress').
        protocol (str): The protocol (e.g., 'tcp', 'udp', '-1' for all).
        from_port (int): The starting port.
        to_port (int): The ending port.
        cidr_blocks (List[str]): List of CIDR blocks.
        provider (aws.Provider): The AWS provider to use.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.SecurityGroupRule: The created security group rule resource.
    """
    if opts is None:
        opts = ResourceOptions()
    rule = aws.ec2.SecurityGroupRule(
        resource_name=rule_name,
        security_group_id=security_group_id,
        type=type,
        protocol=protocol,
        from_port=from_port,
        to_port=to_port,
        cidr_blocks=cidr_blocks,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return rule

def create_ec2_instance(
    instance_name: str,
    ami: str,
    instance_type: str,
    subnet_id: str,
    security_group_ids: List[str],
    aws_provider: aws.Provider,
    key_name: Optional[str] = None,
    opts: ResourceOptions = None,
) -> aws.ec2.Instance:
    """
    Creates an EC2 instance with the specified configuration.

    Args:
        instance_name (str): The name of the EC2 instance.
        ami (str): The AMI ID to use for the instance.
        instance_type (str): The instance type (e.g., 't2.micro').
        subnet_id (str): The ID of the subnet to launch the instance in.
        security_group_ids (List[str]): List of security group IDs.
        provider (aws.Provider): The AWS provider to use.
        key_name (Optional[str]): The name of the SSH key pair.
        opts (ResourceOptions, optional): Pulumi resource options.

    Returns:
        aws.ec2.Instance: The created EC2 instance resource.
    """
    if opts is None:
        opts = ResourceOptions()
    instance = aws.ec2.Instance(
        resource_name=instance_name,
        ami=ami,
        instance_type=instance_type,
        subnet_id=subnet_id,
        vpc_security_group_ids=security_group_ids,
        key_name=key_name,
        opts=opts.merge(ResourceOptions(provider=aws_provider)),
    )
    return instance
