# pulumi/modules/aws/resources.py

"""
This module defines reusable resources for the AWS modules available as type safe functions.

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
# pulumi/modules/aws/resources.py

"""
AWS Module Resource Helpers

This module provides helper functions to create AWS resources using
the configurations defined in the Pydantic-based types.py.
"""

from typing import Dict, List, Any
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, export, log
from .types import (
    ControlTowerConfig,
    IAMUserConfig,
    TenantAccountConfig,
    AWSConfig,
    GlobalTags,
)
from core.metadata import set_global_labels, set_global_annotations
from core.utils import set_resource_metadata


def create_organization() -> aws.organizations.Organization:
    """
    Creates an AWS Organization with all features enabled.

    Returns:
        aws.organizations.Organization: The AWS Organization resource.
    """
    organization = aws.organizations.Organization(
        resource_name="my_organization",
        feature_set="ALL",
        opts=ResourceOptions(protect=True),
    )
    return organization


def create_organizational_units(
    organization: aws.organizations.Organization,
    ou_names: List[str],
) -> Dict[str, aws.organizations.OrganizationalUnit]:
    """
    Creates Organizational Units (OUs) under the specified AWS Organization.

    Args:
        organization (aws.organizations.Organization): The AWS Organization resource.
        ou_names (List[str]): A list of OU names to create.

    Returns:
        Dict[str, aws.organizations.OrganizationalUnit]: A dictionary of OU resources.
    """
    ou_resources = {}
    root_id = organization.roots[0].id

    for ou_name in ou_names:
        ou = aws.organizations.OrganizationalUnit(
            resource_name=f"ou_{ou_name.lower()}",
            name=ou_name,
            parent_id=root_id,
            opts=ResourceOptions(parent=organization),
        )
        ou_resources[ou_name] = ou

    return ou_resources


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


def create_iam_users(iam_users: List[IAMUserConfig], tags: Dict[str, str]) -> None:
    """
    Creates IAM users, groups, and policies as specified in the configuration.

    Args:
        iam_users (List[IAMUserConfig]): A list of IAMUserConfig objects.
        tags (Dict[str, str]): A dictionary of tags to apply to resources.
    """
    for user_config in iam_users:
        # Create IAM User
        iam_user = aws.iam.User(
            resource_name=user_config.name,
            name=user_config.name,
            tags={**tags, "Email": user_config.email},
        )

        # Create IAM Groups and add user to groups
        for group_name in user_config.groups:
            iam_group = aws.iam.Group(
                resource_name=f"group_{group_name}",
                name=group_name,
                tags=tags,
            )
            aws.iam.UserGroupMembership(
                resource_name=f"{user_config.name}_{group_name}_membership",
                user=iam_user.name,
                groups=[iam_group.name],
            )

        # Attach policies to user
        for policy_arn in user_config.policies:
            aws.iam.UserPolicyAttachment(
                resource_name=f"{user_config.name}_{policy_arn.split('/')[-1]}",
                user=iam_user.name,
                policy_arn=policy_arn,
            )


def create_tenant_accounts(
    organization: aws.organizations.Organization,
    ou: aws.organizations.OrganizationalUnit,
    tenant_configs: Dict[str, TenantAccountConfig],
    tags: Dict[str, str],
) -> List[aws.organizations.Account]:
    """
    Creates tenant accounts under the specified Organizational Unit.

    Args:
        organization (aws.organizations.Organization): The AWS Organization resource.
        ou (aws.organizations.OrganizationalUnit): The Organizational Unit resource.
        tenant_configs (Dict[str, TenantAccountConfig]): Tenant account configurations.
        tags (Dict[str, str]): Tags to apply to resources.

    Returns:
        List[aws.organizations.Account]: A list of AWS Account resources representing tenant accounts.
    """
    tenant_accounts = []

    for tenant_name, tenant_config in tenant_configs.items():
        tenant_account = aws.organizations.Account(
            resource_name=f"{tenant_name}_account",
            email=tenant_config.email,
            name=tenant_config.name,
            parent_id=ou.id,
            tags={**tags, **tenant_config.tags},
            opts=ResourceOptions(parent=ou),
        )
        tenant_accounts.append(tenant_account)

    return tenant_accounts


def assume_role_in_tenant_account(
    tenant_account: aws.organizations.Account,
    role_name: str,
    region: str,
) -> aws.Provider:
    """
    Assumes a role in the tenant account to perform operations.

    Args:
        tenant_account (aws.organizations.Account): The tenant AWS account.
        role_name (str): The name of the role to assume.
        region (str): The AWS region.

    Returns:
        aws.Provider: An AWS provider configured to operate in the tenant account.
    """
    role_arn = pulumi.Output.all(tenant_account.id, tenant_account.arn).apply(
        lambda args: f"arn:aws:iam::{args[0]}:role/{role_name}"
    )
    tenant_provider = aws.Provider(
        resource_name=f"tenant_provider_{tenant_account.name}",
        assume_role=aws.ProviderAssumeRoleArgs(
            role_arn=role_arn,
            session_name="PulumiSession",
        ),
        region=region,
        opts=ResourceOptions(parent=tenant_account),
    )
    return tenant_provider


def deploy_tenant_resources(
    tenant_provider: aws.Provider,
    tenant_account: aws.organizations.Account,
    tenant_config: TenantAccountConfig,
    global_tags: Dict[str, str],
) -> None:
    """
    Deploys resources in the tenant account based on the configuration.

    Args:
        tenant_provider (aws.Provider): The AWS provider for the tenant account.
        tenant_account (aws.organizations.Account): The tenant AWS account.
        tenant_config (TenantAccountConfig): Configuration for the tenant account.
        global_tags (Dict[str, str]): Global tags to apply to resources.
    """
    # Implement resource deployment based on tenant_config.features
    # Example: Deploy S3 bucket if 'bucket' feature is enabled
    if 'bucket' in tenant_config.features:
        bucket = aws.s3.Bucket(
            resource_name=f"{tenant_account.name}_bucket",
            bucket=f"{tenant_account.name}-bucket",
            acl="private",
            tags={**global_tags, **tenant_config.tags},
            opts=ResourceOptions(provider=tenant_provider, parent=tenant_account),
        )
        pulumi.export(f"{tenant_account.name}_bucket_name", bucket.bucket)

    # Add more feature-based deployments as needed
    # Example: Deploy EC2 instances if 'ec2' feature is enabled
    if 'ec2' in tenant_config.features:
        ec2_instance = aws.ec2.Instance(
            resource_name=f"{tenant_account.name}_instance",
            ami="ami-0c94855ba95c71c99",  # Example AMI ID; replace with appropriate one
            instance_type="t2.micro",
            tags={**global_tags, **tenant_config.tags},
            opts=ResourceOptions(provider=tenant_provider, parent=tenant_account),
        )
        pulumi.export(f"{tenant_account.name}_instance_id", ec2_instance.id)


def create_vpc(
    vpc_name: str,
    cidr_block: str,
    tags: Dict[str, str],
    provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.Vpc:
    """
    Creates a VPC with the specified configuration.

    Args:
        vpc_name (str): The name of the VPC.
        cidr_block (str): The CIDR block for the VPC.
        tags (Dict[str, str]): Tags to apply to the VPC.
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
        tags=tags,
        enable_dns_hostnames=True,
        enable_dns_support=True,
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return vpc


def create_subnet(
    subnet_name: str,
    cidr_block: str,
    vpc_id: str,
    tags: Dict[str, str],
    provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.Subnet:
    """
    Creates a subnet within the specified VPC.

    Args:
        subnet_name (str): The name of the subnet.
        cidr_block (str): The CIDR block for the subnet.
        vpc_id (str): The ID of the VPC.
        tags (Dict[str, str]): Tags to apply to the subnet.
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
        tags=tags,
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return subnet


def create_security_group(
    sg_name: str,
    vpc_id: str,
    tags: Dict[str, str],
    provider: aws.Provider,
    description: str = "Default security group",
    opts: ResourceOptions = None,
) -> aws.ec2.SecurityGroup:
    """
    Creates a security group within the specified VPC.

    Args:
        sg_name (str): The name of the security group.
        vpc_id (str): The ID of the VPC.
        tags (Dict[str, str]): Tags to apply to the security group.
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
        tags=tags,
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
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return sg


def create_internet_gateway(
    igw_name: str,
    vpc_id: str,
    tags: Dict[str, str],
    provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.InternetGateway:
    """
    Creates an Internet Gateway and attaches it to the specified VPC.

    Args:
        igw_name (str): The name of the Internet Gateway.
        vpc_id (str): The ID of the VPC.
        tags (Dict[str, str]): Tags to apply to the Internet Gateway.
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
        tags=tags,
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return igw


def create_route_table(
    rt_name: str,
    vpc_id: str,
    tags: Dict[str, str],
    provider: aws.Provider,
    opts: ResourceOptions = None,
) -> aws.ec2.RouteTable:
    """
    Creates a route table within the specified VPC.

    Args:
        rt_name (str): The name of the route table.
        vpc_id (str): The ID of the VPC.
        tags (Dict[str, str]): Tags to apply to the route table.
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
        tags=tags,
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return rt


def create_route(
    route_name: str,
    route_table_id: str,
    destination_cidr_block: str,
    gateway_id: str,
    provider: aws.Provider,
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
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return route


def create_subnet_route_table_association(
    association_name: str,
    subnet_id: str,
    route_table_id: str,
    provider: aws.Provider,
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
        opts=opts.merge(ResourceOptions(provider=provider)),
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
    provider: aws.Provider,
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
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return rule


def create_ec2_instance(
    instance_name: str,
    ami: str,
    instance_type: str,
    subnet_id: str,
    security_group_ids: List[str],
    tags: Dict[str, str],
    provider: aws.Provider,
    key_name: str,
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
        tags (Dict[str, str]): Tags to apply to the instance.
        provider (aws.Provider): The AWS provider to use.
        key_name (str): The name of the SSH key pair.
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
        tags=tags,
        key_name=key_name,
        opts=opts.merge(ResourceOptions(provider=provider)),
    )
    return instance
