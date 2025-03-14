# ./modules/aws/eks/networking.py
"""EKS networking infrastructure management."""

from typing import Dict, List, Any
import pulumi_aws as aws
from pulumi import ResourceOptions, log


class NetworkManager:
    """Manages networking infrastructure for EKS clusters."""

    def __init__(self, provider):
        self.provider = provider

    def create_vpc(self, name: str) -> Dict[str, Any]:
        """Create VPC infrastructure for EKS cluster."""
        try:
            vpc = aws.ec2.Vpc(
                f"eks-vpc-{name}",
                cidr_block="10.0.0.0/16",
                enable_dns_hostnames=True,
                enable_dns_support=True,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-vpc-{name}",
                    f"kubernetes.io/cluster/{name}": "shared",
                },
                opts=ResourceOptions(provider=self.provider.provider, parent=self.provider.provider),
            )

            igw = aws.ec2.InternetGateway(
                f"eks-igw-{name}",
                vpc_id=vpc.id,
                tags={
                    **self.provider.get_tags(),
                    "Name": f"eks-igw-{name}",
                },
                opts=ResourceOptions(provider=self.provider.provider, parent=vpc),
            )

            azs = ["us-east-1a", "us-east-1b"]
            public_subnets = []
            private_subnets = []

            for i, az in enumerate(azs):
                public_subnet = aws.ec2.Subnet(
                    f"eks-public-subnet-{name}-{i}",
                    vpc_id=vpc.id,
                    cidr_block=f"10.0.{i*2}.0/24",
                    availability_zone=az,
                    map_public_ip_on_launch=True,
                    tags={
                        **self.provider.get_tags(),
                        "Name": f"eks-public-{name}-{i}",
                        f"kubernetes.io/cluster/{name}": "shared",
                        "kubernetes.io/role/elb": "1",
                    },
                    opts=ResourceOptions(provider=self.provider.provider, parent=vpc),
                )
                public_subnets.append(public_subnet)

                private_subnet = aws.ec2.Subnet(
                    f"eks-private-subnet-{name}-{i}",
                    vpc_id=vpc.id,
                    cidr_block=f"10.0.{i*2+1}.0/24",
                    availability_zone=az,
                    tags={
                        **self.provider.get_tags(),
                        "Name": f"eks-private-{name}-{i}",
                        f"kubernetes.io/cluster/{name}": "shared",
                        "kubernetes.io/role/internal-elb": "1",
                    },
                    opts=ResourceOptions(provider=self.provider.provider, parent=vpc),
                )
                private_subnets.append(private_subnet)

            # Create and configure route tables
            public_rt = self._create_public_route_table(name, vpc, igw)
            nat_gateway = self._create_nat_gateway(name, vpc, public_subnets[0])
            private_rt = self._create_private_route_table(name, vpc, nat_gateway)

            # Associate subnets with route tables
            self._associate_route_tables(name, public_rt, private_rt, public_subnets, private_subnets)

            return {
                "vpc": vpc,
                "public_subnets": public_subnets,
                "private_subnets": private_subnets,
            }

        except Exception as e:
            log.error(f"Failed to create VPC infrastructure: {str(e)}")
            raise

    def _create_public_route_table(
        self, name: str, vpc: aws.ec2.Vpc, igw: aws.ec2.InternetGateway
    ) -> aws.ec2.RouteTable:
        return aws.ec2.RouteTable(
            f"eks-public-rt-{name}",
            vpc_id=vpc.id,
            routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": igw.id}],
            tags={
                **self.provider.get_tags(),
                "Name": f"eks-public-rt-{name}",
            },
            opts=ResourceOptions(provider=self.provider.provider, parent=vpc),
        )

    def _create_nat_gateway(self, name: str, vpc: aws.ec2.Vpc, public_subnet: aws.ec2.Subnet) -> aws.ec2.NatGateway:
        eip = aws.ec2.Eip(
            f"eks-eip-{name}",
            tags={
                **self.provider.get_tags(),
                "Name": f"eks-eip-{name}",
            },
            opts=ResourceOptions(provider=self.provider.provider, parent=vpc),
        )

        return aws.ec2.NatGateway(
            f"eks-nat-{name}",
            allocation_id=eip.id,
            subnet_id=public_subnet.id,
            tags={
                **self.provider.get_tags(),
                "Name": f"eks-nat-{name}",
            },
            opts=ResourceOptions(provider=self.provider.provider, parent=public_subnet),
        )

    def _create_private_route_table(
        self, name: str, vpc: aws.ec2.Vpc, nat_gateway: aws.ec2.NatGateway
    ) -> aws.ec2.RouteTable:
        return aws.ec2.RouteTable(
            f"eks-private-rt-{name}",
            vpc_id=vpc.id,
            routes=[{"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway.id}],
            tags={
                **self.provider.get_tags(),
                "Name": f"eks-private-rt-{name}",
            },
            opts=ResourceOptions(provider=self.provider.provider, parent=vpc),
        )

    def _associate_route_tables(
        self,
        name: str,
        public_rt: aws.ec2.RouteTable,
        private_rt: aws.ec2.RouteTable,
        public_subnets: List[aws.ec2.Subnet],
        private_subnets: List[aws.ec2.Subnet],
    ) -> None:
        for i, subnet in enumerate(public_subnets):
            aws.ec2.RouteTableAssociation(
                f"eks-public-rta-{name}-{i}",
                subnet_id=subnet.id,
                route_table_id=public_rt.id,
                opts=ResourceOptions(provider=self.provider.provider, parent=public_rt),
            )

        for i, subnet in enumerate(private_subnets):
            aws.ec2.RouteTableAssociation(
                f"eks-private-rta-{name}-{i}",
                subnet_id=subnet.id,
                route_table_id=private_rt.id,
                opts=ResourceOptions(provider=self.provider.provider, parent=private_rt),
            )
