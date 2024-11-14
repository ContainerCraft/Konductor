# Konductor Developer Guide

## Introduction

Welcome to the comprehensive developer guide for Konductor! This guide provides detailed information for developers who want to contribute to or extend the Konductor Infrastructure as Code (IaC) platform. Whether you're fixing bugs, adding features, or creating new modules, you'll find everything you need to understand our development practices and standards.

## Table of Contents

1. [Development Environment](#development-environment)
   - [Prerequisites](#prerequisites)
   - [Environment Setup](#environment-setup)
   - [Development Tools](#development-tools)

2. [Core Technologies](#core-technologies)
   - [Pulumi Overview](#pulumi-overview)
   - [Poetry for Dependency Management](#poetry-for-dependency-management)
   - [Type Safety with TypedDict](#type-safety-with-typeddict)
   - [Static Type Checking](#static-type-checking)

3. [Project Structure](#project-structure)
   - [Directory Layout](#directory-layout)
   - [Module Organization](#module-organization)
   - [Configuration Management](#configuration-management)

4. [Development Standards](#development-standards)
   - [Code Style Guidelines](#code-style-guidelines)
   - [Type Annotations](#type-annotations)
   - [Documentation Requirements](#documentation-requirements)
   - [Testing Requirements](#testing-requirements)

5. [Module Development](#module-development)
   - [Module Architecture](#module-architecture)
   - [Creating New Modules](#creating-new-modules)
   - [Module Testing](#module-testing)
   - [Module Documentation](#module-documentation)

6. [Testing and Validation](#testing-and-validation)
   - [Unit Testing](#unit-testing)
   - [Integration Testing](#integration-testing)
   - [Type Checking](#type-checking)
   - [Continuous Integration](#continuous-integration)

7. [Documentation Guidelines](#documentation-guidelines)
   - [Code Documentation](#code-documentation)
   - [Module Documentation](#module-documentation-1)
   - [API Documentation](#api-documentation)
   - [Example Documentation](#example-documentation)

8. [Best Practices](#best-practices)
   - [Code Organization](#code-organization)
   - [Error Handling](#error-handling)
   - [Configuration Management](#configuration-management-1)
   - [Resource Management](#resource-management)

9. [Troubleshooting and Support](#troubleshooting-and-support)
   - [Common Issues](#common-issues)
   - [Getting Help](#getting-help)
   - [Community Resources](#community-resources)

## Development Environment

### Prerequisites

Before starting development, ensure you have:

- Python 3.8 or higher
- Poetry for dependency management
- Pulumi CLI
- Git
- A code editor (VS Code recommended)
- AWS CLI (for AWS module development)
- kubectl (for Kubernetes development)

### Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/containercraft/konductor.git
   cd konductor
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

3. **Activate Virtual Environment**:
   ```bash
   poetry shell
   ```

4. **Configure Development Tools**:
   ```bash
   # Configure Pulumi
   pulumi login

   # Set up pre-commit hooks
   pre-commit install
   ```

### Development Tools

- **VS Code Extensions**:
  - Pylance for Python language support
  - Python extension for debugging
  - YAML extension for configuration files
  - Docker extension for container management

- **Configuration Files**:
  ```json:pyrightconfig.json
  {
    "include": ["**/*.py"],
    "exclude": ["**/__pycache__/**"],
    "reportMissingImports": true,
    "pythonVersion": "3.8",
    "typeCheckingMode": "strict"
  }
  ```

## Core Technologies

### Pulumi Overview

Pulumi is our primary IaC framework, chosen for its:
- Native Python support
- Strong type system integration
- Multi-cloud capabilities
- State management features

### Poetry for Dependency Management

We use Poetry to:
- Manage project dependencies
- Create reproducible builds
- Handle virtual environments
- Package distribution

Example `pyproject.toml`:
```toml
[tool.poetry]
name = "konductor"
version = "0.1.0"
description = "Infrastructure as Code platform"

[tool.poetry.dependencies]
python = "^3.8"
pulumi = "^3.0.0"
pulumi-aws = "^5.0.0"
```

### Type Safety with TypedDict

TypedDict is central to our configuration management:

```python
from typing import TypedDict, List

class ContainerPort(TypedDict):
    containerPort: int
    protocol: str

class Container(TypedDict):
    name: str
    image: str
    ports: List[ContainerPort]
```

### Static Type Checking

We enforce strict type checking using Pyright:

```bash
# Run type checking
poetry run pyright

# Configure VS Code for real-time type checking
{
    "python.analysis.typeCheckingMode": "strict"
}
```

## Project Structure

### Directory Layout

```
konductor/
├── __main__.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── utils.py
└── modules/
│   ├── aws/
│   └── kubernetes/
├── docs/
└── tests/
```

### Module Organization

Each module follows a standard structure:

```
modules/<module_name>/
├── __init__.py
├── types.py
├── deploy.py
├── config.py
└── README.md
```

### Configuration Management

Configuration hierarchy:
1. Default module configurations
2. User-provided configurations
3. Environment-specific overrides

## Development Standards

### Code Style Guidelines

We follow PEP 8 with additional requirements:

```python
# Good
def create_deployment(
    name: str,
    replicas: int,
    container: Container
) -> Deployment:
    """Create a Kubernetes deployment.

    Args:
        name: The deployment name
        replicas: Number of replicas
        container: Container configuration

    Returns:
        The created deployment
    """
    return Deployment(...)

# Bad - Missing type hints and docstring
def create_deployment(name, replicas, container):
    return Deployment(...)
```

### Type Annotations

All code must use type hints:

```python
from typing import Dict, List, Optional

def get_resource_tags(
    environment: str,
    additional_tags: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    tags = {"Environment": environment}
    if additional_tags:
        tags.update(additional_tags)
    return tags
```

### Documentation Requirements

Required documentation elements:
- Module overview
- Function/class docstrings
- Type annotations
- Usage examples
- Configuration options

### Testing Requirements

All code must include:
- Unit tests
- Integration tests (where applicable)
- Type checking validation
- Documentation tests

## Module Development

### Module Architecture

Modules should follow the Single Responsibility Principle:

```python
# Good - Single responsibility
class AwsNetworking:
    """Manages AWS networking resources."""

    def create_vpc(self) -> pulumi.Output[str]:
        """Create a VPC."""
        pass

    def create_subnet(self) -> pulumi.Output[str]:
        """Create a subnet."""
        pass

# Bad - Mixed responsibilities
class AwsResources:
    """Manages various AWS resources."""

    def create_vpc(self) -> str:
        pass

    def create_database(self) -> str:
        pass
```

### Creating New Modules

Follow these steps to create a new module:

1. Create module directory structure
2. Define TypedDict configurations
3. Implement core functionality
4. Add documentation
5. Write tests
6. Submit for review

### Module Testing

Example test structure:

```python
import pytest
from pulumi import automation as auto

def test_vpc_creation():
    """Test VPC creation with default configuration."""
    stack = auto.create_stack(...)

    # Deploy resources
    result = stack.up()

    # Verify outputs
    assert "vpc_id" in result.outputs
    assert result.outputs["vpc_id"].value != ""
```

### Module Documentation

Required module documentation:

1. Overview and purpose
2. Installation instructions
3. Configuration options
4. Usage examples
5. API reference
6. Troubleshooting guide

## Testing and Validation

### Unit Testing

We use pytest for unit testing:

```python
import pytest
from konductor.core.utils import merge_configurations

def test_merge_configurations():
    """Test configuration merging logic."""
    base = {"name": "test", "replicas": 1}
    override = {"replicas": 2}

    result = merge_configurations(base, override)

    assert result["name"] == "test"
    assert result["replicas"] == 2
```

### Integration Testing

Integration tests verify module interactions:

```python
from pulumi import automation as auto
from typing import Generator
import pytest

@pytest.fixture
def pulumi_stack() -> Generator[auto.Stack, None, None]:
    """Create a test stack for integration testing."""
    stack = auto.create_stack(
        stack_name="integration-test",
        project_name="konductor-test"
    )
    yield stack
    stack.destroy()
    stack.workspace.remove_stack("integration-test")

def test_aws_module_integration(pulumi_stack: auto.Stack):
    """Test AWS module integration with core components."""
    # Deploy test infrastructure
    result = pulumi_stack.up()

    # Verify resource creation
    assert "vpc_id" in result.outputs
    assert "subnet_ids" in result.outputs
```

### Type Checking

Run type checking as part of validation:

```bash
# Run type checking with detailed output
poetry run pyright --verbose

# Check specific module
poetry run pyright pulumi/modules/aws
```

### Continuous Integration

Our CI pipeline includes:

1. **Code Quality Checks**:
   ```yaml
   steps:
     - name: Code Quality
       run: |
         poetry run black --check .
         poetry run isort --check-only .
         poetry run flake8 .
   ```

2. **Type Checking**:
   ```yaml
   steps:
     - name: Type Check
       run: poetry run pyright
   ```

3. **Tests**:
   ```yaml
   steps:
     - name: Run Tests
       run: poetry run pytest --cov
   ```

## Documentation Guidelines

### Code Documentation

Follow these docstring conventions:

```python
from typing import Dict, Optional

def update_resource_tags(
    resource_id: str,
    tags: Dict[str, str],
    region: Optional[str] = None
) -> Dict[str, str]:
    """Update tags for an AWS resource.

    Args:
        resource_id: The ID of the resource to update
        tags: Dictionary of tags to apply
        region: Optional AWS region (defaults to current)

    Returns:
        Dictionary of applied tags

    Raises:
        ResourceNotFoundError: If resource doesn't exist
        InvalidTagError: If tags are invalid

    Example:
        >>> tags = update_resource_tags("vpc-123", {"Environment": "prod"})
        >>> assert tags["Environment"] == "prod"
    """
    # Implementation
```

### Module Documentation

Each module must include:

1. **README.md**:
   ```markdown
   # AWS Module

   ## Overview
   Manages AWS infrastructure resources.

   ## Installation
   ```bash
   poetry add konductor-aws
   ```

   ## Usage
   ```python
   from konductor.modules.aws import AwsNetworking

   networking = AwsNetworking(...)
   vpc = networking.create_vpc(...)
   ```

   ## Configuration
   | Parameter | Type | Description | Default |
   |-----------|------|-------------|---------|
   | region | str | AWS region | us-west-2 |
   ```

2. **API Documentation**:
   ```python
   class AwsNetworking:
    """AWS networking resource management.

    Provides functionality for creating and managing AWS networking
    resources including VPCs, subnets, and security groups.

    Attributes:
        region: The AWS region for resource creation
        tags: Default tags for all resources
    """
   ```

### Example Documentation

Provide clear, runnable examples:

```python
from konductor.modules.aws import AwsNetworking
from konductor.core.config import NetworkConfig

# Configuration
network_config = NetworkConfig(
    vpc_cidr="10.0.0.0/16",
    subnet_cidrs=["10.0.1.0/24", "10.0.2.0/24"],
    availability_zones=["us-west-2a", "us-west-2b"]
)

# Create networking resources
networking = AwsNetworking(network_config)
vpc = networking.create_vpc()
subnets = networking.create_subnets()
```

## Best Practices

### Code Organization

1. **Separation of Concerns**:
   ```python
   # Good - Separate configuration and implementation
   class NetworkConfig(TypedDict):
       vpc_cidr: str
       subnet_cidrs: List[str]

   class NetworkManager:
       def __init__(self, config: NetworkConfig):
           self.config = config

   # Bad - Mixed configuration and implementation
   class Network:
       def __init__(self, vpc_cidr: str, subnet_cidrs: List[str]):
           self.create_vpc(vpc_cidr)
           self.create_subnets(subnet_cidrs)
   ```

2. **Resource Organization**:
   ```python
   # Good - Logical resource grouping
   class AwsNetworking:
       def __init__(self, config: NetworkConfig):
           self.vpc = self._create_vpc()
           self.subnets = self._create_subnets()
           self.security_groups = self._create_security_groups()

   # Bad - No clear organization
   class AwsResources:
       def create_stuff(self):
           self.vpc = create_vpc()
           self.database = create_database()
           self.subnets = create_subnets()
   ```

### Error Handling

1. **Custom Exceptions**:
   ```python
   class ResourceError(Exception):
       """Base exception for resource operations."""
       pass

   class ResourceNotFoundError(ResourceError):
       """Raised when a resource cannot be found."""
       pass

   def get_resource(resource_id: str) -> Resource:
       try:
           return fetch_resource(resource_id)
       except ApiError as e:
           raise ResourceNotFoundError(f"Resource {resource_id} not found") from e
   ```

2. **Graceful Degradation**:
   ```python
   from typing import Optional

   def get_resource_tags(
       resource_id: str,
       default: Optional[Dict[str, str]] = None
   ) -> Dict[str, str]:
       """Get resource tags with fallback to defaults."""
       try:
           return fetch_resource_tags(resource_id)
       except ResourceError:
           return default or {}
   ```

### Configuration Management

1. **Configuration Validation**:
   ```python
   from pydantic import BaseModel, Field

   class VpcConfig(BaseModel):
       cidr_block: str = Field(..., regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
       enable_dns: bool = True
       tags: Dict[str, str] = Field(default_factory=dict)
   ```

2. **Environment-Specific Configuration**:
   ```python
   def load_config(environment: str) -> Dict[str, Any]:
       """Load environment-specific configuration."""
       base_config = load_yaml("config/base.yaml")
       env_config = load_yaml(f"config/{environment}.yaml")
       return deep_merge(base_config, env_config)
   ```

### Resource Management

1. **Resource Cleanup**:
   ```python
   class ResourceManager:
       def __init__(self):
           self.resources: List[Resource] = []

       def add_resource(self, resource: Resource):
           self.resources.append(resource)

       def cleanup(self):
           """Clean up all managed resources."""
           for resource in reversed(self.resources):
               try:
                   resource.destroy()
               except ResourceError:
                   logger.exception(f"Failed to cleanup {resource.id}")
   ```

2. **Resource Dependencies**:
   ```python
   class NetworkStack:
       def __init__(self):
           self.vpc = self._create_vpc()
           # Subnets depend on VPC
           self.subnets = self._create_subnets(self.vpc.id)
           # Route tables depend on VPC and subnets
           self.route_tables = self._create_route_tables(
               self.vpc.id,
               self.subnets
           )
   ```

## Troubleshooting and Support

### Common Issues

1. **Type Checking Errors**:
   ```python
   # Error: Parameter "config" missing required TypedDict key "region"
   def deploy(config: AwsConfig):  # Missing region in config
       pass

   # Fix: Provide all required keys
   config: AwsConfig = {
       "region": "us-west-2",
       "tags": {"Environment": "prod"}
   }
   ```

2. **Resource Creation Failures**:
   ```python
   try:
       vpc = create_vpc(config)
   except pulumi.ResourceError as e:
       # Check for common issues
       if "InvalidCidrBlock" in str(e):
           logger.error("Invalid CIDR block specified")
       elif "QuotaExceeded" in str(e):
           logger.error("AWS account quota exceeded")
       raise
   ```

### Getting Help

1. **Community Support**:
   - GitHub Issues: [Konductor Issues](https://github.com/containercraft/konductor/issues)
   - Discord Community: [Join Discord](https://discord.gg/Jb5jgDCksX)
   - Stack Overflow: Tag `konductor`

2. **Documentation Resources**:
   - [User Guide](../user_guide/README.md)
   - [API Reference](../reference/README.md)
   - [Module Documentation](../modules/README.md)

### Community Resources

1. **Contributing**:
   - [Contribution Guidelines](../contribution_guidelines.md)
   - [Code of Conduct](../CODE_OF_CONDUCT.md)
   - [Development Setup](../getting_started.md)

2. **Learning Resources**:
   - [Tutorial Series](../tutorials/README.md)
   - [Example Projects](../examples/README.md)
   - [Best Practices Guide](../reference/best_practices.md)

## Conclusion

This developer guide provides a comprehensive overview of developing with Konductor. Remember to:

- Follow type safety practices
- Write comprehensive tests
- Document your code
- Contribute to the community

For updates and new features, watch our [GitHub repository](https://github.com/containercraft/konductor)
