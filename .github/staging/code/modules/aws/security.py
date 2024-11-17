# pulumi/modules/aws/security.py

"""
AWS Security Management Module

Handles creation and management of AWS security resources including:
- KMS keys and key policies
- Security group management
- WAF configurations
- Certificate management
- Secret management
- Security Hub enablement
"""

from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
import json
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, log
from .iam import IAMManager
from pulumi_aws import Provider
from pulumi_aws.cloudtrail import Trail
from .types import AWSConfig

if TYPE_CHECKING:
    from .types import SecurityConfig
    from .provider import AWSProvider

class SecurityManager:
    """
    Manages AWS security resources and operations.

    This class handles:
    - KMS key management
    - Security group configurations
    - WAF and security rules
    - Certificate and secret management
    - Security Hub and GuardDuty
    """

    def __init__(self, provider: 'AWSProvider'):
        """
        Initialize Security manager.

        Args:
            provider: AWSProvider instance for resource management
        """
        self.provider = provider

    def create_kms_key(
        self,
        name: str,
        description: str,
        key_usage: str = "ENCRYPT_DECRYPT",
        deletion_window: int = 30,
        enable_key_rotation: bool = True,
        policy: Optional[Dict[str, Any]] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.kms.Key:
        """
        Creates a KMS key with specified configuration.

        Args:
            name: Key name
            description: Key description
            key_usage: Key usage type
            deletion_window: Key deletion window in days
            enable_key_rotation: Enable automatic key rotation
            policy: Key policy document
            opts: Optional resource options

        Returns:
            aws.kms.Key: Created KMS key
        """
        if opts is None:
            opts = ResourceOptions()

        # Create the KMS key
        key = aws.kms.Key(
            f"key-{name}",
            description=description,
            deletion_window_in_days=deletion_window,
            enable_key_rotation=enable_key_rotation,
            key_usage=key_usage,
            policy=json.dumps(policy) if policy else None,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Create an alias for the key
        aws.kms.Alias(
            f"alias-{name}",
            name=f"alias/{name}",
            target_key_id=key.id,
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=key,
                protect=True
            )
        )

        return key

    def create_certificate(
        self,
        domain_name: str,
        validation_method: str = "DNS",
        subject_alternative_names: Optional[List[str]] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.acm.Certificate:
        """
        Creates an ACM certificate.

        Args:
            domain_name: Primary domain name
            validation_method: Certificate validation method
            subject_alternative_names: Additional domain names
            opts: Optional resource options

        Returns:
            aws.acm.Certificate: Created certificate
        """
        if opts is None:
            opts = ResourceOptions()

        certificate = aws.acm.Certificate(
            f"cert-{domain_name}",
            domain_name=domain_name,
            validation_method=validation_method,
            subject_alternative_names=subject_alternative_names,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        return certificate

    def create_secret(
        self,
        name: str,
        secret_string: Union[str, Dict[str, Any]],
        description: Optional[str] = None,
        kms_key_id: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.secretsmanager.Secret:
        """
        Creates a Secrets Manager secret.

        Args:
            name: Secret name
            secret_string: Secret value or dictionary
            description: Secret description
            kms_key_id: KMS key ID for encryption
            opts: Optional resource options

        Returns:
            aws.secretsmanager.Secret: Created secret
        """
        if opts is None:
            opts = ResourceOptions()

        # Create the secret
        secret = aws.secretsmanager.Secret(
            f"secret-{name}",
            name=name,
            description=description,
            kms_key_id=kms_key_id,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

        # Create the secret version
        secret_string_value = (
            json.dumps(secret_string)
            if isinstance(secret_string, dict)
            else secret_string
        )

        aws.secretsmanager.SecretVersion(
            f"secret-version-{name}",
            secret_id=secret.id,
            secret_string=secret_string_value,
            opts=ResourceOptions(
                provider=self.provider.provider,
                parent=secret,
                protect=True
            )
        )

        return secret

    def enable_security_hub(
        self,
        enable_default_standards: bool = True,
        control_findings_visible: bool = True,
        opts: Optional[ResourceOptions] = None
    ) -> aws.securityhub.Account:
        """
        Enables AWS Security Hub for the account.

        Args:
            enable_default_standards: Enable default security standards
            control_findings_visible: Make findings visible
            opts: Optional resource options

        Returns:
            aws.securityhub.Account: Security Hub account configuration
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.securityhub.Account(
            "security-hub",
            enable_default_standards=enable_default_standards,
            control_findings_visible=control_findings_visible,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def enable_guardduty(
        self,
        enable_s3_logs: bool = True,
        opts: Optional[ResourceOptions] = None
    ) -> aws.guardduty.Detector:
        """
        Enables Amazon GuardDuty for the account.

        Args:
            enable_s3_logs: Enable S3 log monitoring
            opts: Optional resource options

        Returns:
            aws.guardduty.Detector: GuardDuty detector
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.guardduty.Detector(
            "guardduty-detector",
            enable=True,
            finding_publishing_frequency="ONE_HOUR",
            datasources=aws.guardduty.DetectorDatasourcesArgs(
                s3_logs=aws.guardduty.DetectorDatasourcesS3LogsArgs(
                    enable=enable_s3_logs
                )
            ),
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_waf_web_acl(
        self,
        name: str,
        rules: List[Dict[str, Any]],
        description: Optional[str] = None,
        scope: str = "REGIONAL",
        opts: Optional[ResourceOptions] = None
    ) -> aws.wafv2.WebAcl:
        """
        Creates a WAFv2 Web ACL.

        Args:
            name: Web ACL name
            rules: List of WAF rules
            description: Web ACL description
            scope: WAF scope (REGIONAL or CLOUDFRONT)
            opts: Optional resource options

        Returns:
            aws.wafv2.WebAcl: Created Web ACL
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.wafv2.WebAcl(
            f"waf-{name}",
            name=name,
            description=description,
            scope=scope,
            default_action=aws.wafv2.WebAclDefaultActionArgs(
                allow=aws.wafv2.WebAclDefaultActionAllowArgs()
            ),
            rules=rules,
            visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name=f"waf-{name}-metric",
                sampled_requests_enabled=True
            ),
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_cloudwatch_log_group(
        self,
        name: str,
        retention_days: int = 30,
        kms_key_id: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.cloudwatch.LogGroup:
        """
        Creates a CloudWatch Log Group.

        Args:
            name: Log group name
            retention_days: Log retention period
            kms_key_id: KMS key for encryption
            opts: Optional resource options

        Returns:
            aws.cloudwatch.LogGroup: Created log group
        """
        if opts is None:
            opts = ResourceOptions()

        return aws.cloudwatch.LogGroup(
            f"log-group-{name}",
            name=name,
            retention_in_days=retention_days,
            kms_key_id=kms_key_id,
            tags=self.provider.get_tags(),
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

    def create_cloudtrail(
        self,
        name: str,
        s3_bucket_name: str,
        include_global_events: bool = True,
        is_multi_region: bool = True,
        kms_key_id: Optional[str] = None,
        log_group_name: Optional[str] = None,
        opts: Optional[ResourceOptions] = None
    ) -> aws.cloudtrail.Trail:
        """
        Creates a CloudTrail trail.

        Args:
            name: Trail name
            s3_bucket_name: S3 bucket for logs
            include_global_events: Include global service events
            is_multi_region: Enable multi-region trail
            kms_key_id: KMS key for encryption
            log_group_name: CloudWatch log group name
            opts: Optional resource options

        Returns:
            aws.cloudtrail.Trail: Created trail
        """
        if opts is None:
            opts = ResourceOptions()

        # Create CloudWatch log group if specified
        log_group = None
        role = None  # Initialize role variable
        if log_group_name:
            log_group = self.create_cloudwatch_log_group(
                log_group_name,
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=opts.parent if opts else None
                )
            )

            # Create IAM role for CloudTrail to CloudWatch Logs
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }]
            }

            role = aws.iam.Role(
                f"cloudtrail-cloudwatch-role-{name}",
                assume_role_policy=json.dumps(assume_role_policy),
                tags=self.provider.get_tags(),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=log_group
                )
            )

            # Attach policy to role
            aws.iam.RolePolicy(
                f"cloudtrail-cloudwatch-policy-{name}",
                role=role.id,
                policy=pulumi.Output.all(log_group_arn=log_group.arn).apply(
                    lambda args: json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": f"{args['log_group_arn']}:*"
                        }]
                    })
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=role
                )
            )

        # Create the trail
        trail_args = {
            "name": name,
            "s3_bucket_name": s3_bucket_name,
            "include_global_service_events": include_global_events,
            "is_multi_region_trail": is_multi_region,
            "kms_key_id": kms_key_id,
            "tags": self.provider.get_tags()
        }

        if log_group and role:  # Add check for both resources
            trail_args.update({
                "cloud_watch_logs_group_arn": pulumi.Output.concat(log_group.arn, ":*"),
                "cloud_watch_logs_role_arn": role.arn
            })

        return aws.cloudtrail.Trail(
            f"trail-{name}",
            **trail_args,
            opts=ResourceOptions.merge(
                ResourceOptions(
                    provider=self.provider.provider,
                    protect=True
                ),
                opts
            )
        )

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

def setup_cloudtrail(
    config: AWSConfig,
    provider: Provider,
    depends_on: Optional[List[pulumi.Resource]] = None
) -> Trail:
    """
    Sets up AWS CloudTrail for audit logging.

    Args:
        config: AWS configuration
        provider: AWS provider
        depends_on: Optional resource dependencies

    Returns:
        aws.cloudtrail.Trail: Configured CloudTrail

    TODO:
    - Enhance log encryption
    - Add log validation
    - Implement log analysis
    - Add automated alerting
    - Enhance retention policies
    """
    try:
        # Create S3 bucket for CloudTrail logs
        trail_bucket = aws.s3.Bucket(
            "cloudtrail-logs",
            force_destroy=True,
            opts=ResourceOptions(
                provider=provider,
                depends_on=depends_on,
                protect=True
            )
        )

        # Create CloudTrail
        trail = aws.cloudtrail.Trail(
            "audit-trail",
            s3_bucket_name=trail_bucket.id,
            include_global_service_events=True,
            is_multi_region_trail=True,
            enable_logging=True,
            opts=ResourceOptions(
                provider=provider,
                depends_on=[trail_bucket],
                protect=True
            )
        )

        return trail

    except Exception as e:
        pulumi.log.error(f"Error setting up CloudTrail: {str(e)}")
        raise
