# ./modules/aws/eks/iam.py
"""IAM role management for EKS clusters."""

import json
from typing import Optional
import pulumi_aws as aws
from pulumi import ResourceOptions, log


class IamRoleManager:
    """Manages IAM roles for EKS clusters."""

    def __init__(self, provider):
        self.provider = provider

    def create_cluster_role(self, name: str) -> aws.iam.Role:
        """Create the IAM role for the EKS cluster control plane."""
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "eks.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }

        role = aws.iam.Role(
            f"eks-cluster-role-{name}",
            assume_role_policy=json.dumps(assume_role_policy),
            tags=self.provider.get_tags(),
            opts=ResourceOptions(provider=self.provider.provider, parent=self.provider.provider),
        )

        aws.iam.RolePolicyAttachment(
            f"eks-cluster-policy-{name}",
            policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
            role=role.name,
            opts=ResourceOptions(provider=self.provider.provider, parent=role),
        )

        return role

    def create_node_role(self, name: str) -> aws.iam.Role:
        """Create the IAM role for EKS worker nodes."""
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}
            ],
        }

        role = aws.iam.Role(
            f"eks-node-role-{name}",
            assume_role_policy=json.dumps(assume_role_policy),
            tags=self.provider.get_tags(),
            opts=ResourceOptions(provider=self.provider.provider, parent=self.provider.provider),
        )

        required_policies = ["AmazonEKSWorkerNodePolicy", "AmazonEKS_CNI_Policy", "AmazonEC2ContainerRegistryReadOnly"]

        for policy in required_policies:
            aws.iam.RolePolicyAttachment(
                f"eks-node-policy-{policy}-{name}",
                policy_arn=f"arn:aws:iam::aws:policy/{policy}",
                role=role.name,
                opts=ResourceOptions(provider=self.provider.provider, parent=role),
            )

        return role
