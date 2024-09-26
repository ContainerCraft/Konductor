# Project Roadmap: Comprehensive AWS Organization and IAM Management with Pulumi

## Introduction
This project aims to develop a comprehensive AWS Organization and IAM Management program using Pulumi and Python. It will focus on demonstrating high-quality AWS infrastructure automation setups, including AWS Organizations, Control Tower, IAM policies, roles, users, groups, and associated permissions. The primary audience for this project is senior platform engineering teams who require real-world, scalable, and modular infrastructure automation solutions.

## Goals and Objectives
- Demonstrate the setup of an AWS Organization with nested Organizational Units (OUs).
- Implement AWS Control Tower for multi-account governance.
- Configure and manage IAM roles, policies, users, and groups.
- Adopt best practices for infrastructure as code (IaC), including modular code, thorough documentation, and type-safe configurations.

## Plan of Action

### 1. Code Structure and Modules
1. **Core Module**: Handles configuration management, deployment orchestration, metadata management, and utility functions.
2. **Infrastructure Module**: Manages AWS-specific resources, including AWS Organization, Control Tower, IAM roles, policies, users, groups, and their permissions.
3. **Utils Module**: Provides helper functions for common tasks and resource transformations.

### 2. Defining Configuration Structures
1. **Configuration File (Pulumi.aws.yaml)**:
   - Centralize all configurations, including AWS Organization details, Control Tower settings, IAM configurations, and global tags.
   - Use nested structures to define tenant accounts, workloads, and associated tags.

2. **Type-Safe Data Classes**:
   - Define data classes for AWS configurations using Python's `dataclasses` module.
   - Ensure type safety and clarity by using well-defined data structures.

### 3. AWS Organization Setup
1. **Creating AWS Organizations**:
   - Define a function to create AWS Organizations with all features enabled.

```python
def create_organization() -> aws.organizations.Organization:
    """
    Creates an AWS Organization with all features enabled.

    Returns:
        aws.organizations.Organization: The AWS Organization resource.
    """
    organization = aws.organizations.Organization("my_organization", feature_set="ALL", opts=ResourceOptions(protect=True))
    return organization
```

2. **Creating Organizational Units (OUs)**:
   - Define a function to create OUs under the specified AWS Organization.

```python
def create_organizational_units(organization: aws.organizations.Organization, config: ControlTowerConfig) -> Dict[str, aws.organizations.OrganizationalUnit]:
    """
    Creates Organizational Units (OUs) under the specified AWS Organization.

    Args:
        organization: The AWS Organization resource.
        config: ControlTowerConfig - Configuration parameters for Control Tower.

    Returns:
        Dict[str, aws.organizations.OrganizationalUnit]: Dictionary of Organizational Unit resources.
    """
    organizational_units = {}
    for ou_name in config.managed_organizational_unit_names:
        ou = aws.organizations.OrganizationalUnit(f"ou_{ou_name.lower()}", name=ou_name, parent_id=organization.roots[0].id, opts=ResourceOptions(parent=organization))
        organizational_units[ou_name] = ou
    return organizational_units
```

### 4. AWS Control Tower Setup
1. **Enabling AWS Control Tower**:
   - Placeholder function to enable AWS Control Tower (hypothetical until AWS provides full programmatic support).

### 5. IAM Management
1. **Creating IAM Roles and Policies**:
   - Define functions to create IAM roles for Control Tower and other specific needs.
   - Attach necessary policies to these roles.

```python
def create_iam_roles(config: ControlTowerConfig) -> Dict[str, aws.iam.Role]:
    """
    Creates IAM roles required by AWS Control Tower.

    Args:
        config: ControlTowerConfig - Configuration parameters for Control Tower.

    Returns:
        Dict[str, aws.iam.Role]: Dictionary of IAM Role resources.
    """
    iam_roles = {}

    # Control Tower Admin Role
    admin_role = aws.iam.Role(
        "control_tower_admin_role",
        name=config.control_tower_admin_role_name,
        assume_role_policy="""{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "controltower.amazonaws.com"}, "Action": "sts:AssumeRole"}]}""",
        tags=global_tags.__dict__
    )
    aws.iam.RolePolicyAttachment("admin_role_policy_attachment", role=admin_role.name, policy_arn="arn:aws:iam::aws:policy/AdministratorAccess")

    iam_roles["admin_role"] = admin_role

    # Control Tower Execution Role
    execution_role = aws.iam.Role(
        "control_tower_execution_role",
        name=config.control_tower_execution_role_name,
        assume_role_policy="""{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": "*"}, "Action": "sts:AssumeRole"}]}""",
        tags=global_tags.__dict__
    )
    aws.iam.RolePolicyAttachment("execution_role_policy_attachment", role=execution_role.name, policy_arn="arn:aws:iam::aws:policy/AWSControlTowerExecution")

    iam_roles["execution_role"] = execution_role

    return iam_roles
```

2. **Creating and Managing IAM Users**:
   - Define functions to create IAM users, assign them to groups, and attach policies.

```python
def create_iam_resources(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig) -> None:
    """
    Creates IAM users, groups, roles, and policies in the tenant account.

    Args:
        tenant_provider: aws.Provider - The AWS Provider configured for the tenant account.
        tenant_account: aws.organizations.Account - The AWS Account resource representing the tenant account.
        config: TenantAccountConfig - Configuration parameters for tenant account.
    """
    # Create an IAM Group
    developers_group = aws.iam.Group(f"{tenant_account.name}_developers_group", name="Developers", path="/teams/", opts=ResourceOptions(provider=tenant_provider, parent=tenant_account))

    # Create an IAM Policy
    developers_policy = aws.iam.Policy(f"{tenant_account.name}_developers_policy", name="DevelopersPolicy", path="/policies/", description="Policy for developers group.", policy="""{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": ["ec2:Describe*", "s3:List*"], "Resource": "*"}]}""", opts=ResourceOptions(provider=tenant_provider, parent=developers_group))

    # Attach the Policy to the Group
    aws.iam.GroupPolicyAttachment(f"{tenant_account.name}_developers_policy_attachment", group=developers_group.name, policy_arn=developers_policy.arn, opts=ResourceOptions(provider=tenant_provider, parent=developers_group))

    # Create IAM Users and add them to the Group
    for user_name in ["alice", "bob"]:
        iam_user = aws.iam.User(f"{tenant_account.name}_user_{user_name}", name=user_name, path="/users/", tags={"Name": user_name, "Department": "Engineering"}, opts=ResourceOptions(provider=tenant_provider, parent=tenant_account))
        aws.iam.UserGroupMembership(f"{tenant_account.name}_user_{user_name}_group_membership", user=iam_user.name, groups=[developers_group.name], opts=ResourceOptions(provider=tenant_provider, parent=iam_user))
```

### 6. Deploying Workloads in Tenant Accounts
1. **Deploying Various Workloads**:
   - Define functions for deploying EKS clusters, RDS instances, Lambda functions, etc.
   - Utilize tenant-specific AWS Providers for these deployments.

```python
def deploy_workload(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig) -> None:
    """
    Deploys workloads in the tenant account based on the specified workload type.

    Args:
        tenant_provider: aws.Provider - The AWS Provider configured for the tenant account.
        tenant_account: aws.organizations.Account - The AWS Account resource representing the tenant account.
        config: TenantAccountConfig - Configuration parameters for tenant account.
    """
    workload_type = config.workload
    if workload_type == "eks_cluster":
        deploy_eks_cluster(tenant_provider, tenant_account, config)
    elif workload_type == "rds_instance":
        deploy_rds_instance(tenant_provider, tenant_account, config)
    elif workload_type == "lambda_function":
        deploy_lambda_function(tenant_provider, tenant_account, config)
    else:
        pulumi.log.warn(f"No workload defined for {tenant_account.name}")

def deploy_eks_cluster(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig) -> None:
    # Implement deployment of EKS Cluster
    ...

def deploy_rds_instance(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig) -> None:
    # Implement deployment of RDS Instance
    ...

def deploy_lambda_function(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig) -> None:
    # Implement deployment of Lambda Function
    ...
```

### 7. Secrets Management
1. **Creating Secrets in AWS Secrets Manager**:
   - Define a function to create secrets in AWS Secrets Manager for tenant accounts.

```python
def create_secrets(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account) -> None:
    """
    Creates secrets in AWS Secrets Manager in the tenant account.

    Args:
        tenant_provider: aws.Provider - The AWS Provider configured for the tenant account.
        tenant_account: aws.organizations.Account - The AWS Account resource representing the tenant account.
    """
    secret = aws.secretsmanager.Secret(
        f"{tenant_account.name}_secret",
        name=f"{tenant_account.name}-Secret",
        description="A secret for demo purposes",
        tags=global_tags.__dict__,
        opts=ResourceOptions(provider=tenant_provider, parent=tenant_account)
    )
    aws.secretsmanager.SecretVersion(
        f"{tenant_account.name}_secret_version",
        secret_id=secret.id,
        secret_string="SuperSecretValue",  # Replace with actual secret value
        opts=ResourceOptions(provider=tenant_provider, parent=secret)
    )
    pulumi.export(f"{tenant_account.name}_secret_arn", secret.arn)
```

### 8. Main Execution and Resource Management
1. **Main Execution Function**:
   - Define the main function to call all other functions in sequence, ensuring appropriate dependencies and order of execution.

```python
def main():
    organization = create_organization()

    if control_tower_config.enable_control_tower:
        enable_control_tower(control_tower_config)

    organizational_units = create_organizational_units(organization, control_tower_config)
    iam_roles = create_iam_roles(control_tower_config)
    tenant_accounts = create_tenant_accounts(organizational_units[control_tower_config.organizational_unit_name], tenant_account_configs)

    apply_control_tower_controls(tenant_accounts)

    for tenant_account in tenant_accounts:
        tenant_provider = aws.Provider(
            f"tenant_provider_{tenant_account.name}",
            assume_role=aws.ProviderAssumeRoleArgs(
                role_arn=tenant_account.arn.apply(
                    lambda arn: arn.replace("arn:aws:organizations::", "arn:aws:iam::").replace(":account/", ":role/OrganizationAccountAccessRole")
                ),
                session_name="PulumiSession"
            ),
            region=control_tower_config.region,
            opts=ResourceOptions(parent=tenant_account)
        )

        config = tenant_account_configs[tenant_account.name.lower()]
        create_iam_resources(tenant_provider, tenant_account, config)
        deploy_workload(tenant_provider, tenant_account, config)
        create_secrets(tenant_provider, tenant_account)

        pulumi.export(f"{tenant_account.name}_id", tenant_account.id)

    for ou_name, ou in organizational_units.items():
        pulumi.export(f"organizational_unit_{ou_name}_id", ou.id)

    pulumi.export("control_tower_admin_role_arn", iam_roles["admin_role"].arn)
    pulumi.export("control_tower_execution_role_arn", iam_roles["execution_role"].arn)

if __name__ == "__main__":
    main()
```

### 9. Documentation and Best Practices
1. **Comprehensive Docstrings and Comments**:
   - Ensure all functions and classes are well-documented with detailed docstrings and inline comments.

2. **Developer Guide**:
   - Create a detailed developer guide to explain the project structure, codebase, and contribution guidelines.

### 10. Testing and Validation
1. **Unit Testing**:
   - Write unit tests for critical functions to ensure functionality and prevent regressions.

2. **Integration Testing**:
   - Deploy the infrastructure in a test environment and validate its correctness and robustness.

3. **Error Handling**:
   - Implement robust error handling and logging to aid in troubleshooting and debugging.
