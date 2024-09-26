# Developer Guide

## Introduction

This document is intended for developers who want to contribute to the Pulumi AWS Infrastructure Automation codebase. It provides insights into the code structure, development best practices, and the contribution workflow.

## Table of Contents

1. [Code Structure](#code-structure)
2. [Development Best Practices](#development-best-practices)
3. [Contribution Workflow](#contribution-workflow)
4. [Adding Enhancements and Features](#adding-enhancements-and-features)
5. [Testing and Validation](#testing-and-validation)
6. [Documentation Standards](#documentation-standards)
7. [Support and Resources](#support-and-resources)

## Code Structure

The project is organized into modular functions to ensure code scalability and maintainability. Below is an overview of the key components:

- **`aws_types.py`**: Defines type-safe dataclasses for AWS resource functions.
- **`aws_deploy.py`**: Contains the main Pulumi program with functions for AWS Organization, Control Tower, IAM, workloads, and secrets management.
- **`README.md`**: Provides setup and usage instructions.
- **`DEVELOPER.md`**: Guide for developers contributing to the project.
- **`requirements.txt`**: Lists the dependencies for the project.
- **`Pulumi.dev.yaml`**: Configuration file for Pulumi Stack settings.

### Example Directory Structure

```
~/drive/Git/ccio/konductor  refactor ❯ tree pulumi -I __pycache__
pulumi
├── CALL_TO_ACTION.md
├── README.md
├── __main__.py
├── core
│   ├── README.md
│   ├── __init__.py
│   ├── config.py
│   ├── deployment.py
│   ├── metadata.py
│   ├── resource_helpers.py
│   ├── types.py
│   └── utils.py
├── default_versions.json
├── modules
│   ├── README.md
│   ├── aws
│   │   ├── ROADMAP.md
│   │   ├── DEVELOPER.md
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── types.py
│   ├── azure
│   │   └── __init__.py
│   ├── cert_manager
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── types.py
│   ├── cilium
│   │   ├── __init__.py
│   │   └── deploy.py
│   ├── cluster_network_addons
│   │   ├── __init__.py
│   │   └── deploy.py
│   ├── containerized_data_importer
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── types.py
│   ├── hostpath_provisioner
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── types.py
│   ├── kubernetes_dashboard
│   │   ├── __init__.py
│   │   └── deploy.py
│   ├── kubevirt
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── types.py
│   ├── kv_manager
│   │   ├── __init__.py
│   │   └── deploy.py
│   ├── multus
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── types.py
│   ├── openunison
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   └── encoded_assets.py
│   └── prometheus
│       ├── __init__.py
│       ├── deploy.py
│       └── types.py
├── requirements.txt
└── stacks
    ├── Pulumi.aws.yaml
    └── Pulumi.ci.yaml
```

## Development Best Practices

### Code Hygiene

- **Modularization**: Break down functions and logic into small, reusable components for better maintainability.
- **Docstrings and Comments**: Document code extensively using docstrings and inline comments. This ensures clarity and understanding for current and future developers.
- **Error Handling**: Implement error handling to catch and manage exceptions gracefully.
- **Resource Options**: Use `ResourceOptions` to manage resource dependencies and parent-child relationships.

### Naming Conventions

- Use `snake_case` for function and variable names.
- Use `PascalCase` for class names.
- Use descriptive names that clearly indicate the function's or variable's purpose.

### Environment Configuration

Store configuration parameters in separate configuration files (e.g., `configurations.py`) and update `Pulumi.dev.yaml` with necessary stack settings.

## Contribution Workflow

### Fork and Clone the Repository

1. Fork the repository on GitHub.
2. Clone the forked repository to your local machine.
   ```sh
   git clone https://github.com/your-username/pulumi-aws-infrastructure.git
   cd pulumi-aws-infrastructure
   ```

### Set Up Development Environment

1. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

2. **Configure Pulumi**:
   ```sh
   pulumi login
   pulumi stack init dev
   ```

3. **Set Up AWS Credentials**:
   ```sh
   aws configure
   ```

### Create a Feature Branch

1. Create a new branch for your feature or bugfix.
   ```sh
   git checkout -b feature/new-feature
   ```

2. Create a new branch for your feature or bugfix.
   ```bash
   # Pulumi stack initialization
   pulumi stack init dev

   # Configure your AWS profile and region
   pulumi config set aws:profile <Your-AWS-Profile>
   pulumi config set aws:region <Your-AWS-Region>

   # Run the deployment
   pulumi up
  ```

### Implement Changes

1. Add or modify code in the appropriate modules.
2. Ensure new functionality is well-documented with docstrings and comments.
3. Write tests for your changes (if applicable).

### Commit and Push

1. Commit your changes with a clear and concise commit message.
   ```sh
   git add .
   git commit -m "Add new feature: description"
   ```

2. Push your changes to your forked repository.
   ```sh
   git push origin feature/new-feature
   ```

### Create a Pull Request

1. Go to the original repository on GitHub and open a pull request from your feature branch.
2. Provide a detailed description of the changes made and any relevant context or documentation.

## Adding Enhancements and Features

### Example: Adding a New Workload (S3)

1. **Define Configuration Parameters**:
   Add new parameters for the S3 workload in `aws_deploy.py`.
   ```python
   tenant_account_configs["tenant4"] = TenantAccountConfig(
       email="tenant4@example.com",
       name="TenantAccount4",
       workload="s3_bucket",
       tags={"Environment": "QA", "Department": "Data"}
   )
   ```

2. **Extend Deployment Logic**:
   Add a function to deploy an S3 bucket in `aws_deploy.py`.
   ```python
   def deploy_s3_bucket(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig):
       bucket = aws.s3.Bucket(
           f"{tenant_account.name}_s3_bucket",
           bucket=f"{tenant_account.name}-bucket",
           acl="private",
           tags={**global_tags.__dict__, **config.tags},
           opts=ResourceOptions(provider=tenant_provider, parent=tenant_account)
       )
       export(f"{tenant_account.name}_s3_bucket_name", bucket.bucket)
   ```

3. **Update Deployment Dispatcher**:
   Update the `deploy_workload` function in `aws_deploy.py` to include the new workload type.
   ```python
   def deploy_workload(tenant_provider: aws.Provider, tenant_account: aws.organizations.Account, config: TenantAccountConfig):
       workload_type = config.workload
       if workload_type == "eks_cluster":
           deploy_eks_cluster(tenant_provider, tenant_account, config)
       elif workload_type == "rds_instance":
           deploy_rds_instance(tenant_provider, tenant_account, config)
       elif workload_type == "lambda_function":
           deploy_lambda_function(tenant_provider, tenant_account, config)
       elif workload_type == "s3_bucket":
           deploy_s3_bucket(tenant_provider, tenant_account, config)
       else:
           print(f"No workload defined for {tenant_account.name}")
   ```
