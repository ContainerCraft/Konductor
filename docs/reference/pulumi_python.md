# Pulumi Python Development Standards

## Table of Contents

1. [Introduction](#introduction)
2. [Development Philosophy](#development-philosophy)
3. [Environment Setup](#environment-setup)
4. [Code Organization](#code-organization)
5. [Type Safety](#type-safety)
6. [Configuration Management](#configuration-management)
7. [Development Standards](#development-standards)
8. [Testing Requirements](#testing-requirements)
9. [Documentation Requirements](#documentation-requirements)
10. [Best Practices](#best-practices)
11. [Appendices](#appendices)

## Introduction

This document establishes the development standards and best practices for Pulumi Python projects within the Konductor framework. It serves as the authoritative reference for code quality, maintainability, and consistency across all modules and components.

### Core Principles

- **Type Safety**: Enforce static type checking for reliability
- **Maintainability**: Write clear, documented, and testable code
- **Consistency**: Follow established patterns and standards
- **Quality**: Prioritize code quality over feature quantity

## Development Philosophy

> "Features are nice. Quality is paramount."

Our development approach emphasizes:

1. **Code Quality**:
   - Comprehensive type checking
   - Clear documentation
   - Thorough testing
   - Consistent style

2. **Developer Experience**:
   - Intuitive interfaces
   - Clear error messages
   - Helpful documentation
   - Streamlined workflows

3. **Maintainability**:
   - Modular design
   - Single responsibility
   - Clear dependencies
   - Consistent patterns

## Environment Setup

### Prerequisites

- Python 3.8+
- Poetry for dependency management
- Pulumi CLI
- Pyright for type checking
- Git for version control

### Initial Setup

1. **Install Poetry**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Configure Poetry**:
   ```bash
   poetry config virtualenvs.in-project true
   ```

3. **Initialize Project**:
   ```bash
   poetry install
   poetry shell
   ```

4. **Configure Pulumi**:
   ```yaml
   # Pulumi.yaml
   name: your-project
   runtime:
     name: python
     options:
       toolchain: poetry
       typechecker: pyright
   ```

## Code Organization

### Directory Structure

```
project/
├── pulumi/
│   ├── __main__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── utils.py
│   └── modules/
│       ├── aws/
│       │   ├── __init__.py
│       │   ├── types.py
│       │   └── deploy.py
│       └── kubernetes/
│           ├── __init__.py
│           ├── types.py
│           └── deploy.py
├── tests/
├── pyproject.toml
├── poetry.lock
└── pyrightconfig.json
```

### Module Structure

Each module should follow this structure:

```python
# types.py
from typing import TypedDict

class ModuleConfig(TypedDict):
    """Configuration schema for the module."""
    enabled: bool
    version: str
    parameters: Dict[str, Any]

# deploy.py
def deploy_module(
    config: ModuleConfig,
    dependencies: List[Resource]
) -> Resource:
    """Deploy module resources."""
    pass
```

## Type Safety

### TypedDict Usage

1. **Configuration Schemas**:
   ```python
   from typing import TypedDict, Optional

   class NetworkConfig(TypedDict):
       """Network configuration schema."""
       vpc_cidr: str
       subnet_cidrs: List[str]
       enable_nat: bool
       tags: Optional[Dict[str, str]]
   ```

2. **Default Values**:
   ```python
   network_defaults: NetworkConfig = {
       "vpc_cidr": "10.0.0.0/16",
       "subnet_cidrs": [],
       "enable_nat": True,
       "tags": None
   }
   ```

### Type Checking

1. **Configure Pyright**:
   ```json
   {
     "include": ["**/*.py"],
     "exclude": ["**/__pycache__/**"],
     "reportMissingImports": true,
     "pythonVersion": "3.8",
     "typeCheckingMode": "strict"
   }
   ```

2. **Run Type Checking**:
   ```bash
   poetry run pyright
   ```

## Configuration Management

### Configuration Structure

1. **Module Configurations**:
   ```python
   class ModuleConfig(TypedDict):
       enabled: bool
       version: str
       parameters: Dict[str, Any]

   def load_config(
       module_name: str,
       config: pulumi.Config
   ) -> ModuleConfig:
       """Load and validate module configuration."""
       pass
   ```

2. **Validation**:
   ```python
   def validate_config(config: ModuleConfig) -> None:
       """Validate configuration values."""
       if not isinstance(config["enabled"], bool):
           raise TypeError("enabled must be a boolean")
   ```

## Development Standards

### Code Style

1. **Naming Conventions**:
   - Classes: `PascalCase`
   - Functions/Variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`
   - Private members: `_leading_underscore`

2. **Documentation**:
   ```python
   def create_resource(
       name: str,
       config: ResourceConfig
   ) -> Resource:
       """Create a new resource.

       Args:
           name: Resource name
           config: Resource configuration

       Returns:
           Created resource

       Raises:
           ValueError: If configuration is invalid
       """
       pass
   ```

3. **Error Handling**:
   ```python
   try:
       resource = create_resource(name, config)
   except ValueError as e:
       pulumi.log.error(f"Failed to create resource: {e}")
       raise
   ```

### Function Signatures

1. **Type Annotations**:
   ```python
   from typing import Optional, List, Dict, Any

   def deploy_resources(
       configs: List[ResourceConfig],
       dependencies: Optional[List[Resource]] = None,
       **kwargs: Any
   ) -> List[Resource]:
       """Deploy multiple resources."""
       pass
   ```

2. **Return Types**:
   ```python
   def get_resource_status(
       resource_id: str
   ) -> Optional[Dict[str, Any]]:
       """Get resource status or None if not found."""
       pass
   ```

## Testing Requirements

### Unit Tests

1. **Test Structure**:
   ```python
   import pytest
   from typing import Generator

   @pytest.fixture
   def resource_config() -> Generator[ResourceConfig, None, None]:
       """Provide test configuration."""
       config = create_test_config()
       yield config
       cleanup_test_config(config)

   def test_resource_creation(
       resource_config: ResourceConfig
   ) -> None:
       """Test resource creation."""
       result = create_resource("test", resource_config)
       assert result.id is not None
   ```

2. **Mocking**:
   ```python
   @pytest.fixture
   def mock_aws_client(mocker):
       """Mock AWS client."""
       return mocker.patch("boto3.client")
   ```

### Integration Tests

```python
def test_module_deployment(
    pulumi_stack: auto.Stack
) -> None:
    """Test full module deployment."""
    result = pulumi_stack.up()
    assert result.summary.resource_changes["create"] > 0
```

## Documentation Requirements

### Code Documentation

1. **Module Documentation**:
   ```python
   """AWS networking module.

   This module manages AWS networking resources including VPCs,
   subnets, and security groups.

   Example:
       ```python
       config = NetworkConfig(...)
       vpc = create_vpc(config)
       ```
   """
   ```

2. **Function Documentation**:
   ```python
   def create_vpc(
       config: NetworkConfig,
       tags: Optional[Dict[str, str]] = None
   ) -> Resource:
       """Create a VPC with the specified configuration.

       Args:
           config: VPC configuration
           tags: Optional resource tags

       Returns:
           Created VPC resource

       Raises:
           ValueError: If CIDR is invalid
       """
       pass
   ```

## Best Practices

1. **Resource Management**:
   ```python
   def create_resources(
       configs: List[ResourceConfig]
   ) -> List[Resource]:
       """Create multiple resources with proper cleanup."""
       resources = []
       try:
           for config in configs:
               resource = create_resource(config)
               resources.append(resource)
           return resources
       except Exception:
           cleanup_resources(resources)
           raise
   ```

2. **Configuration Handling**:
   ```python
   def load_config(
       path: str,
       defaults: Dict[str, Any]
   ) -> Dict[str, Any]:
       """Load configuration with defaults."""
       config = load_yaml(path)
       return deep_merge(defaults, config)
   ```

3. **Error Handling**:
   ```python
   class ResourceError(Exception):
       """Base exception for resource operations."""
       pass

   class ResourceNotFoundError(ResourceError):
       """Raised when a resource cannot be found."""
       pass
   ```

## Appendices

### A. Common Patterns

1. **Resource Tags**:
   ```python
   def get_resource_tags(
       name: str,
       environment: str,
       additional_tags: Optional[Dict[str, str]] = None
   ) -> Dict[str, str]:
       """Generate standard resource tags."""
       tags = {
           "Name": name,
           "Environment": environment,
           "ManagedBy": "pulumi"
       }
       if additional_tags:
           tags.update(additional_tags)
       return tags
   ```

2. **Resource Names**:
   ```python
   def generate_resource_name(
       base_name: str,
       suffix: Optional[str] = None
   ) -> str:
       """Generate consistent resource names."""
       name = f"{base_name}-{pulumi.get_stack()}"
       if suffix:
           name = f"{name}-{suffix}"
       return name.lower()
   ```

### B. Type Checking Examples

```python
from typing import TypedDict, Optional, List, Dict, Any

class ResourceConfig(TypedDict):
    """Resource configuration."""
    name: str
    type: str
    parameters: Dict[str, Any]
    tags: Optional[Dict[str, str]]

def create_resource(
    config: ResourceConfig,
    dependencies: Optional[List[Resource]] = None
) -> Resource:
    """Create a resource with type checking."""
    validate_config(config)
    return Resource(
        config["name"],
        config["parameters"],
        opts=ResourceOptions(depends_on=dependencies)
    )
```

### C. Testing Patterns

```python
import pytest
from pulumi import automation as auto

def test_infrastructure_deployment():
    """Test full infrastructure deployment."""
    stack = auto.create_stack(...)
    try:
        result = stack.up()
        assert result.summary.result == "succeeded"
    finally:
        stack.destroy()
        stack.workspace.remove_stack(stack.name)
```
