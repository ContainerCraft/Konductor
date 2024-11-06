# pulumi/modules/aws/iam.py

"""
AWS IAM Management Module

Handles creation and management of IAM resources including:
- Users, Groups, and Roles
- Policies and Policy Attachments
- Cross-account access roles
- Service-linked roles
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import json
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log

if TYPE_CHECKING:
    from .types import IAMUserConfig
    from .provider import AWSProvider

class IAMManager:
    """
    Manages AWS IAM resources and operations.

    This class handles:
    - User and group management
    - Role and policy management
    - Cross-account access configuration
    - Service role management
    """

    def __init__(self, provider: 'AWSProvider'):
        """
        Initialize IAM manager.

        Args:
            provider: AWSProvider instance for resource management
        """
        self.provider = provider

    def create_user(
        self,
        config: IAMUserConfig,
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.User:
        """
        Creates an IAM user with associated groups and policies.

        Args:
            config: IAM user configuration
            opts: Optional resource options

        Returns:
            aws.iam.User: Created IAM user resource
        """
        if opts is None:
            opts = ResourceOptions()

        # Create the IAM user
        user = aws.iam.User(
            f"user-{config.name}",
            name=config.name,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Create login profile if email is provided
        if config.email:
            aws.iam.UserLoginProfile(
                f"login-{config.name}",
                user=user.name,
                password_reset_required=True,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=user,
                    protect=True
                )
            )

        # Attach user to groups
        for group_name in config.groups:
            self.add_user_to_group(user, group_name)

        # Attach policies
        for policy_arn in config.policies:
            self.attach_user_policy(user, policy_arn)

        return user

    def create_group(
        self,
        name: str,
        policies: Optional[List[str]] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.Group:
        """
        Creates an IAM group with attached policies.

        Args:
            name: Group name
            policies: List of policy ARNs to attach
            opts: Optional resource options

        Returns:
            aws.iam.Group: Created IAM group
        """
        if opts is None:
            opts = ResourceOptions()

        group = aws.iam.Group(
            f"group-{name}",
            name=name,
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        if policies:
            for policy_arn in policies:
                aws.iam.GroupPolicyAttachment(
                    f"policy-{name}-{policy_arn.split('/')[-1]}",
                    group=group.name,
                    policy_arn=policy_arn,
                    opts=ResourceOptions(
                        provider=self.provider.provider,
                        parent=group,
                        protect=True
                    )
                )

        return group

    def create_role(
        self,
        name: str,
        assume_role_policy: Dict[str, Any],
        policies: Optional[List[str]] = None,
        description: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.Role:
        """
        Creates an IAM role with specified trust and permission policies.

        Args:
            name: Role name
            assume_role_policy: Trust policy document
            policies: List of policy ARNs to attach
            description: Optional role description
            opts: Optional resource options

        Returns:
            aws.iam.Role: Created IAM role
        """
        if opts is None:
            opts = ResourceOptions()

        role = aws.iam.Role(
            f"role-{name}",
            name=name,
            assume_role_policy=json.dumps(assume_role_policy),
            description=description,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        if policies:
            for policy_arn in policies:
                aws.iam.RolePolicyAttachment(
                    f"policy-{name}-{policy_arn.split('/')[-1]}",
                    role=role.name,
                    policy_arn=policy_arn,
                    opts=ResourceOptions(
                        provider=self.provider.provider,
                        parent=role,
                        protect=True
                    )
                )

        return role

    def create_policy(
        self,
        name: str,
        policy_document: Dict[str, Any],
        description: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.Policy:
        """
        Creates an IAM policy.

        Args:
            name: Policy name
            policy_document: Policy document
            description: Optional policy description
            opts: Optional resource options

        Returns:
            aws.iam.Policy: Created IAM policy
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.iam.Policy(
            f"policy-{name}",
            name=name,
            policy=json.dumps(policy_document),
            description=description,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_service_linked_role(
        self,
        aws_service_name: str,
        description: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.ServiceLinkedRole:
        """
        Creates a service-linked role for AWS services.

        Args:
            aws_service_name: AWS service name (e.g., 'eks.amazonaws.com')
            description: Optional role description
            opts: Optional resource options

        Returns:
            aws.iam.ServiceLinkedRole: Created service-linked role
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.iam.ServiceLinkedRole(
            f"slr-{aws_service_name.split('.')[0]}",
            aws_service_name=aws_service_name,
            description=description,
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_cross_account_role(
        self,
        name: str,
        trusted_account_id: str,
        policies: List[str],
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.Role:
        """
        Creates a role for cross-account access.

        Args:
            name: Role name
            trusted_account_id: AWS account ID to trust
            policies: List of policy ARNs to attach
            opts: Optional resource options

        Returns:
            aws.iam.Role: Created cross-account role
        """
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{trusted_account_id}:root"
                },
                "Action": "sts:AssumeRole"
            }]
        }

        return self.create_role(
            name=name,
            assume_role_policy=assume_role_policy,
            policies=policies,
            description=f"Cross-account access role for {trusted_account_id}",
            opts=opts
        )

    def add_user_to_group(
        self,
        user: aws.iam.User,
        group_name: str
    ) -> aws.iam.UserGroupMembership:
        """
        Adds a user to an IAM group.

        Args:
            user: IAM user resource
            group_name: Name of the group

        Returns:
            aws.iam.UserGroupMembership: Group membership resource
        """
        return aws.iam.UserGroupMembership(
            f"membership-{user.name}-{group_name}",
            user=user.name,
            groups=[group_name],
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=user,
                protect=True
            )
        )

    def attach_user_policy(
        self,
        user: aws.iam.User,
        policy_arn: str
    ) -> aws.iam.UserPolicyAttachment:
        """
        Attaches a policy to an IAM user.

        Args:
            user: IAM user resource
            policy_arn: ARN of the policy to attach

        Returns:
            aws.iam.UserPolicyAttachment: Policy attachment resource
        """
        return aws.iam.UserPolicyAttachment(
            f"policy-{user.name}-{policy_arn.split('/')[-1]}",
            user=user.name,
            policy_arn=policy_arn,
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=user,
                protect=True
            )
        )

    def create_instance_profile(
        self,
        name: str,
        role: aws.iam.Role,
        opts: Optional[ResourceOptions] = None
    ) -> aws.iam.InstanceProfile:
        """
        Creates an instance profile for EC2 instances.

        Args:
            name: Profile name
            role: IAM role to associate
            opts: Optional resource options

        Returns:
            aws.iam.InstanceProfile: Created instance profile
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.iam.InstanceProfile(
            f"profile-{name}",
            name=name,
            role=role.name,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    parent=role,
                    protect=True
                ),
                opts
            )
        )
