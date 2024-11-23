# pulumi/modules/aws/networking.py

"""
AWS Networking Management Module

Handles creation and management of AWS networking resources including:
- VPCs and subnets
- Route tables and routes
- Security groups and rules
- Internet and NAT gateways
- Network ACLs
- VPC endpoints
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log
from .security import SecurityManager

if TYPE_CHECKING:
    from .types import NetworkConfig
    from .provider import AWSProvider

class NetworkManager:
    """
    Manages AWS networking resources and operations.

    This class handles:
    - VPC and subnet management
    - Routing configuration
    - Security group management
    - Gateway provisioning
    - Network ACL configuration
    """

    def __init__(self, provider: 'AWSProvider'):
        """
        Initialize Network manager.

        Args:
            provider: AWSProvider instance for resource management
        """
        self.provider = provider

    def create_vpc(
        self,
        name: str,
        cidr_block: str,
        enable_dns_hostnames: bool = True,
        enable_dns_support: bool = True,
        instance_tenancy: str = "default",
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.Vpc:
        """
        Creates a VPC with the specified configuration.

        Args:
            name: VPC name
            cidr_block: CIDR block for the VPC
            enable_dns_hostnames: Enable DNS hostnames
            enable_dns_support: Enable DNS support
            instance_tenancy: Default instance tenancy
            opts: Optional resource options

        Returns:
            aws.ec2.Vpc: Created VPC resource
        """
        # Add flow logs configuration
        def enable_vpc_flow_logs(self, vpc: aws.ec2.Vpc) -> aws.ec2.FlowLog:
            log_group = aws.cloudwatch.LogGroup(...)
            return aws.ec2.FlowLog(
                f"flow-log-{vpc.id}",
                vpc_id=vpc.id,
                traffic_type="ALL",
                log_destination=log_group.arn,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=vpc
                )
            )

        if opts is None:
            opts = ResourceOptions()

        vpc = aws.ec2.Vpc(
            f"vpc-{name}",
            cidr_block=cidr_block,
            enable_dns_hostnames=enable_dns_hostnames,
            enable_dns_support=enable_dns_support,
            instance_tenancy=instance_tenancy,
            tags={
                **self.provider.get_tags(),
                "Name": f"vpc-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Enable VPC flow logs by default
        self.enable_vpc_flow_logs(vpc)

        return vpc

    def enable_vpc_flow_logs(
        self,
        vpc: aws.ec2.Vpc,
        retention_days: int = 7
    ) -> aws.ec2.FlowLog:
        """
        Enables VPC flow logs.

        Args:
            vpc: VPC resource
            retention_days: Log retention period in days

        Returns:
            aws.ec2.FlowLog: Flow log resource
        """
        # Create log group for flow logs
        log_group = aws.cloudwatch.LogGroup(
            f"flow-logs-{vpc.id}",
            retention_in_days=retention_days,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=vpc
            )
        )

        # Create IAM role for flow logs
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "vpc-flow-logs.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        }

        role = aws.iam.Role(
            f"flow-logs-role-{vpc.id}",
            assume_role_policy=pulumi.Output.from_input(assume_role_policy).apply(lambda x: pulumi.Output.json_dumps(x)),
            tags=self.provider.get_tags(),
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=vpc
            )
        )

        # Attach policy to role
        aws.iam.RolePolicy(
            f"flow-logs-policy-{vpc.id}",
            role=role.id,
            policy=pulumi.Output.all(log_group_arn=log_group.arn).apply(
                lambda args: pulumi.Output.json_dumps({
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "logs:DescribeLogGroups",
                            "logs:DescribeLogStreams"
                        ],
                        "Resource": [
                            args["log_group_arn"],
                            f"{args['log_group_arn']}:*"
                        ]
                    }]
                })
            ),
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=role
            )
        )

        # Create flow log
        return aws.ec2.FlowLog(
            f"flow-log-{vpc.id}",
            vpc_id=vpc.id,
            traffic_type="ALL",
            iam_role_arn=role.arn,
            log_destination=log_group.arn,
            tags=self.provider.get_tags(),
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=vpc
            )
        )

    def create_subnet(
        self,
        name: str,
        vpc_id: pulumi.Input[str],
        cidr_block: str,
        availability_zone: str,
        map_public_ip: bool = False,
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.Subnet:
        """
        Creates a subnet in the specified VPC.

        Args:
            name: Subnet name
            vpc_id: VPC ID
            cidr_block: CIDR block for the subnet
            availability_zone: AZ for the subnet
            map_public_ip: Auto-assign public IPs
            opts: Optional resource options

        Returns:
            aws.ec2.Subnet: Created subnet resource
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.ec2.Subnet(
            f"subnet-{name}",
            vpc_id=vpc_id,
            cidr_block=cidr_block,
            availability_zone=availability_zone,
            map_public_ip_on_launch=map_public_ip,
            tags={
                **self.provider.get_tags(),
                "Name": f"subnet-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_internet_gateway(
        self,
        name: str,
        vpc_id: pulumi.Input[str],
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.InternetGateway:
        """
        Creates and attaches an internet gateway to a VPC.

        Args:
            name: Gateway name
            vpc_id: VPC ID
            opts: Optional resource options

        Returns:
            aws.ec2.InternetGateway: Created internet gateway
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.ec2.InternetGateway(
            f"igw-{name}",
            vpc_id=vpc_id,
            tags={
                **self.provider.get_tags(),
                "Name": f"igw-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_nat_gateway(
        self,
        name: str,
        subnet_id: pulumi.Input[str],
        opts: Optional[ResourceOptions] = None
    ) -> Tuple[aws.ec2.Eip, aws.ec2.NatGateway]:
        """
        Creates a NAT gateway with an Elastic IP.

        Args:
            name: Gateway name
            subnet_id: Subnet ID for the NAT gateway
            opts: Optional resource options

        Returns:
            Tuple containing:
                - Elastic IP resource
                - NAT Gateway resource
        """
        if opts is None:
            opts = ResourceOptions()

        eip = aws.ec2.Eip(
            f"eip-{name}",
            vpc=True,
            tags={
                **self.provider.get_tags(),
                "Name": f"eip-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        nat_gateway = aws.ec2.NatGateway(
            f"nat-{name}",
            subnet_id=subnet_id,
            allocation_id=eip.id,
            tags={
                **self.provider.get_tags(),
                "Name": f"nat-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True,
                    depends_on=[eip]
                ),
                opts
            )
        )

        return eip, nat_gateway

    def create_route_table(
        self,
        name: str,
        vpc_id: pulumi.Input[str],
        routes: Optional[List[Dict[str, Any]]] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.RouteTable:
        """
        Creates a route table with specified routes.

        Args:
            name: Route table name
            vpc_id: VPC ID
            routes: List of route configurations
            opts: Optional resource options

        Returns:
            aws.ec2.RouteTable: Created route table
        """
        if opts is None:
            opts = ResourceOptions()

        route_table = aws.ec2.RouteTable(
            f"rt-{name}",
            vpc_id=vpc_id,
            tags={
                **self.provider.get_tags(),
                "Name": f"rt-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        if routes:
            for idx, route in enumerate(routes):
                aws.ec2.Route(
                    f"route-{name}-{idx}",
                    route_table_id=route_table.id,
                    destination_cidr_block=route.get("destination_cidr_block"),
                    gateway_id=route.get("gateway_id"),
                    nat_gateway_id=route.get("nat_gateway_id"),
                    opts=ResourceOptions(
                        provider=self.provider.provider,
                        parent=route_table
                    )
                )

        return route_table

    def create_security_group(
        self,
        name: str,
        vpc_id: pulumi.Input[str],
        description: str,
        ingress_rules: Optional[List[Dict[str, Any]]] = None,
        egress_rules: Optional[List[Dict[str, Any]]] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.SecurityGroup:
        """
        Creates a security group with specified rules.

        Args:
            name: Security group name
            vpc_id: VPC ID
            description: Security group description
            ingress_rules: List of ingress rule configurations
            egress_rules: List of egress rule configurations
            opts: Optional resource options

        Returns:
            aws.ec2.SecurityGroup: Created security group
        """
        if opts is None:
            opts = ResourceOptions()

        security_group = aws.ec2.SecurityGroup(
            f"sg-{name}",
            vpc_id=vpc_id,
            description=description,
            tags={
                **self.provider.get_tags(),
                "Name": f"sg-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        if ingress_rules:
            for idx, rule in enumerate(ingress_rules):
                aws.ec2.SecurityGroupRule(
                    f"sgr-{name}-ingress-{idx}",
                    type="ingress",
                    security_group_id=security_group.id,
                    protocol=rule.get("protocol", "tcp"),
                    from_port=rule.get("from_port"),
                    to_port=rule.get("to_port"),
                    cidr_blocks=rule.get("cidr_blocks"),
                    source_security_group_id=rule.get("source_security_group_id"),
                    opts=ResourceOptions(
                        provider=self.provider.provider,
                        parent=security_group
                    )
                )

        if egress_rules:
            for idx, rule in enumerate(egress_rules):
                aws.ec2.SecurityGroupRule(
                    f"sgr-{name}-egress-{idx}",
                    type="egress",
                    security_group_id=security_group.id,
                    protocol=rule.get("protocol", "-1"),
                    from_port=rule.get("from_port", 0),
                    to_port=rule.get("to_port", 0),
                    cidr_blocks=rule.get("cidr_blocks", ["0.0.0.0/0"]),
                    opts=ResourceOptions(
                        provider=self.provider.provider,
                        parent=security_group
                    )
                )

        return security_group

    def create_vpc_endpoint(
        self,
        name: str,
        vpc_id: pulumi.Input[str],
        service_name: str,
        subnet_ids: Optional[List[pulumi.Input[str]]] = None,
        security_group_ids: Optional[List[pulumi.Input[str]]] = None,
        vpc_endpoint_type: str = "Interface",
        private_dns_enabled: bool = True,
        opts: Optional[ResourceOptions] = None
    ) -> aws.ec2.VpcEndpoint:
        """
        Creates a VPC endpoint for AWS services.

        Args:
            name: Endpoint name
            vpc_id: VPC ID
            service_name: AWS service name
            subnet_ids: List of subnet IDs for the endpoint
            security_group_ids: List of security group IDs
            vpc_endpoint_type: Endpoint type (Interface/Gateway)
            private_dns_enabled: Enable private DNS
            opts: Optional resource options

        Returns:
            aws.ec2.VpcEndpoint: Created VPC endpoint
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.ec2.VpcEndpoint(
            f"vpce-{name}",
            vpc_id=vpc_id,
            service_name=service_name,
            vpc_endpoint_type=vpc_endpoint_type,
            subnet_ids=subnet_ids,
            security_group_ids=security_group_ids,
            private_dns_enabled=private_dns_enabled,
            tags={
                **self.provider.get_tags(),
                "Name": f"vpce-{name}"
            },
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def deploy_network_infrastructure(self) -> Dict[str, Any]:
        """Deploys networking infrastructure and returns outputs."""
        try:
            # Create VPC
            vpc = self.create_vpc(
                "main",
                self.provider.config.network.vpc_cidr
            )

            # Create subnets
            subnets = []
            for i, az in enumerate(self.provider.config.network.availability_zones):
                subnet = self.create_subnet(
                    f"subnet-{i}",
                    vpc.id,
                    self.provider.config.network.subnet_cidrs["private"][i],
                    az,
                    opts=ResourceOptions(
                        provider=self.provider.provider,
                        parent=vpc
                    )
                )
                subnets.append(subnet)

            return {
                "vpc_id": vpc.id,
                "subnet_ids": [s.id for s in subnets]
            }

        except Exception as e:
            log.error(f"Failed to deploy network infrastructure: {str(e)}")
            raise
