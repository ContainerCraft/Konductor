# TypedDict Reference Guide for Konductor

## Introduction

This reference guide provides comprehensive documentation on using `TypedDict` within the Konductor Infrastructure as Code (IaC) platform. `TypedDict`, introduced in PEP 589, is central to Konductor's configuration management strategy, providing type-safe dictionary structures that enhance code reliability and maintainability.

## Table of Contents

1. [Overview](#overview)
   - [Why TypedDict?](#why-typeddict)
   - [Benefits in Konductor](#benefits-in-konductor)
   - [Integration with Pulumi](#integration-with-pulumi)

2. [Using TypedDict in Konductor](#using-typeddict-in-konductor)
   - [Basic Usage](#basic-usage)
   - [Advanced Patterns](#advanced-patterns)
   - [Best Practices](#best-practices)

3. [Configuration Management](#configuration-management)
   - [Module Configurations](#module-configurations)
   - [Default Values](#default-values)
   - [Configuration Validation](#configuration-validation)

4. [Type Checking](#type-checking)
   - [Static Analysis with Pyright](#static-analysis-with-pyright)
   - [Runtime Considerations](#runtime-considerations)
   - [Common Type Issues](#common-type-issues)

5. [Examples](#examples)
   - [Basic Examples](#basic-examples)
   - [Module Examples](#module-examples)
   - [Complex Configurations](#complex-configurations)

6. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
   - [Best Practices](#best-practices-1)
   - [FAQs](#faqs)

## Overview

### Why TypedDict?

`TypedDict` provides several key advantages for configuration management in Konductor:

- **Type Safety**: Catch configuration errors at development time
- **IDE Support**: Enhanced autocompletion and type hints
- **Documentation**: Self-documenting configuration structures
- **Validation**: Static type checking for configurations
- **Maintainability**: Clear contract for configuration objects

### Benefits in Konductor

In Konductor, `TypedDict` is used to:

1. Define module configurations
2. Specify resource properties
3. Structure complex data hierarchies
4. Ensure configuration consistency
5. Facilitate static analysis

### Integration with Pulumi

`TypedDict` integrates seamlessly with Pulumi's Python SDK:

```python
from typing import TypedDict, List
from pulumi import ResourceOptions

class ResourceConfig(TypedDict):
    name: str
    tags: dict
    opts: ResourceOptions
```

## Using TypedDict in Konductor

### Basic Usage

Define configuration schemas using `TypedDict`:

```python
from typing import TypedDict, Optional

class ModuleConfig(TypedDict):
    enabled: bool
    version: Optional[str]
    namespace: str
    labels: dict

# Default configuration
module_defaults: ModuleConfig = {
    "enabled": False,
    "version": None,
    "namespace": "default",
    "labels": {}
}
```

### Advanced Patterns

#### Nested Configurations

```python
class ContainerPort(TypedDict):
    containerPort: int
    protocol: str

class Container(TypedDict):
    name: str
    image: str
    ports: List[ContainerPort]

class PodSpec(TypedDict):
    containers: List[Container]
```

#### Optional Fields

```python
from typing import TypedDict, Optional

class AwsConfig(TypedDict, total=False):
    region: str  # Required
    profile: Optional[str]  # Optional
    tags: dict  # Optional
```

### Best Practices

1. **Use Clear Names**:
   ```python
   # Good
   class NetworkConfig(TypedDict):
       vpc_cidr: str
       subnet_cidrs: List[str]

   # Avoid
   class Config(TypedDict):
       cidr: str
       subnets: List[str]
   ```

2. **Document Fields**:
   ```python
   class DeploymentConfig(TypedDict):
       """Configuration for Kubernetes deployments.

       Attributes:
           name: Name of the deployment
           replicas: Number of desired replicas
           image: Container image to deploy
       """
       name: str
       replicas: int
       image: str
   ```

3. **Provide Defaults**:
   ```python
   deployment_defaults: DeploymentConfig = {
       "name": "app",
       "replicas": 1,
       "image": "nginx:latest"
   }
   ```

## Configuration Management

### Module Configurations

Each module defines its configuration schema:

```python
# modules/aws/types.py
class AwsModuleConfig(TypedDict):
    enabled: bool
    region: str
    profile: Optional[str]
    tags: Dict[str, str]

# Default configuration
aws_defaults: AwsModuleConfig = {
    "enabled": False,
    "region": "us-west-2",
    "profile": None,
    "tags": {}
}
```

### Default Values

Implement default value handling:

```python
def merge_with_defaults(
    user_config: dict,
    defaults: TypedDict
) -> TypedDict:
    """Merge user configuration with defaults."""
    config = defaults.copy()
    config.update(user_config)
    return config
```

### Configuration Validation

Use Pyright for static validation:

```json
# Configure in pyrightconfig.json
{
    "typeCheckingMode": "strict",
    "reportUnknownMemberType": true
}
```

## Type Checking

### Static Analysis with Pyright

Enable strict type checking:

```json
{
    "include": ["/.py"],
    "exclude": ["/_pycache_/"],
    "reportMissingImports": true,
    "pythonVersion": "3.8",
    "typeCheckingMode": "strict"
}
```

### Runtime Considerations

`TypedDict` performs no runtime validation:

```python
from typing import cast

def load_config(config_dict: dict) -> ModuleConfig:
    """Load and validate configuration.
    Note: TypedDict casting provides no runtime checks.
    Add explicit validation if needed.
    """
    config = cast(ModuleConfig, config_dict)
    validate_config(config)  # Add custom validation if needed
    return config
```

### Common Type Issues

1. **Missing Required Fields**:
   ```python
   # Error: Missing required 'name' field
   config: ModuleConfig = {
       "enabled": True
   }
   ```

2. **Incorrect Types**:
   ```python
   # Error: 'enabled' must be bool
   config: ModuleConfig = {
       "enabled": "true",  # Should be True
       "name": "test"
   }
   ```

## Examples

### Basic Examples

```python
from typing import TypedDict, List

class ServiceConfig(TypedDict):
    name: str
    port: int
    replicas: int

# Usage
service_config: ServiceConfig = {
    "name": "web",
    "port": 80,
    "replicas": 3
}
```

### Module Examples

```python
# AWS VPC Configuration
class VpcConfig(TypedDict):
    cidr_block: str
    enable_dns: bool
    tags: Dict[str, str]

# Kubernetes Deployment
class DeploymentConfig(TypedDict):
    name: str
    namespace: str
    replicas: int
    image: str
    ports: List[int]
```

### Complex Configurations

```python
class DatabaseConfig(TypedDict):
    engine: str
    version: str
    size: str
    backup: bool

class ApplicationConfig(TypedDict):
    name: str
    environment: str
    replicas: int
    database: DatabaseConfig
    features: Dict[str, bool]
```

## Troubleshooting

### Common Issues

1. **Type Mismatch Errors**:
   ```python
   # Error: Type mismatch
   config: NetworkConfig = {
       "vpc_cidr": 10,  # Should be str
       "subnet_cidrs": ["10.0.0.0/24"]
   }
   ```

2. **Missing Fields**:
   ```python
   # Error: Missing required field
   config: ServiceConfig = {
       "name": "api"  # Missing required 'port' field
   }
   ```

### Best Practices

1. Use explicit type annotations
2. Provide default values
3. Document configuration schemas
4. Use static type checking
5. Implement custom validation when needed

### FAQs

**Q: When should I use TypedDict vs. dataclass?**
A: Use TypedDict when working with dictionary-like structures, especially for configurations. Use dataclasses for more complex objects with methods.

**Q: How do I handle optional fields?**
A: Use `total=False` or wrap types with `Optional[]`.

**Q: Can I use TypedDict with Pulumi outputs?**
A: Yes, but be aware that Pulumi outputs are handled differently than regular values.

## Related Documentation

- [Python Development Standards](./PULUMI_PYTHON.md)
- [Style Guide](./style_guide.md)
- [Developer Guide](../developer_guide/konductor_developer_guide.md)
