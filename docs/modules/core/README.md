# Konductor Core Module Documentation

## Introduction

The **Konductor Core Module** serves as the foundational framework for the Konductor Infrastructure as Code (IaC) platform built with Pulumi and Python. It provides essential core functionalities including:

- Configuration management with layered inheritance and validation
- Deployment orchestration with dynamic module loading
- Resource management and transformation handling
- Compliance controls and metadata propagation
- Git integration and repository metadata tracking
- Type-safe interfaces and data structures

This documentation serves as a comprehensive guide for developers, DevOps practitioners, module maintainers, and contributors, enabling them to effectively utilize and extend the core module's capabilities.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Core Module Components](#core-module-components)
4. [Configuration Management](#configuration-management)
5. [Initialization Flow](#initialization-flow)
6. [Deployment Orchestration](#deployment-orchestration)
7. [Metadata and Tagging](#metadata-and-tagging)
8. [Resource Management Helpers](#resource-management-helpers)
9. [Type Definitions and Schemas](#type-definitions-and-schemas)
10. [Git Integration](#git-integration)
11. [Interfaces and Protocols](#interfaces-and-protocols)
12. [Utility Functions](#utility-functions)
13. [Usage Guidelines](#usage-guidelines)
14. [Best Practices](#best-practices)
15. [Development Guidelines](#development-guidelines)
16. [Testing and Validation](#testing-and-validation)
17. [Contribution Guidelines](#contribution-guidelines)
18. [Related Documentation](#related-documentation)

## Architecture Overview

### Directory Structure

The core module follows a carefully organized structure that promotes clarity, maintainability, and separation of concerns:

```plaintext
core/
├── __init__.py             # Module initialization and public API
├── initialization.py       # Pulumi initialization and configuration loading
├── config.py              # Configuration management and validation
├── deployment.py          # Deployment orchestration and module management
├── metadata.py            # Global metadata and tagging utilities
├── git.py                # Git utilities for repository information
├── types.py              # Type definitions and data models
├── interfaces.py         # Protocol and interface definitions
└── utils.py              # General utility functions
```

### Design Philosophy

The core module adheres to the following architectural principles:

1. **Separation of Concerns**
   - Each component handles a specific aspect of infrastructure management
   - Clear boundaries between different functionalities
   - Modular design for easier maintenance and testing

2. **Type Safety**
   - Comprehensive use of type hints and annotations
   - Pydantic models for configuration validation
   - TypedDict for structured data typing
   - Runtime type checking integration

3. **Configuration Isolation**
   - Layered configuration system with inheritance
   - Module-specific configuration validation
   - Default configurations with override capabilities
   - Environment-specific configuration support

4. **Resource Abstraction**
   - Consistent resource creation patterns
   - Global resource transformations
   - Standardized metadata application
   - Resource dependency management

5. **Compliance Integration**
   - Built-in compliance controls
   - Automated metadata tagging
   - Audit trail generation
   - Security policy enforcement

6. **Git Integration**
   - Automatic Git metadata collection
   - Repository information tracking
   - Deployment versioning
   - Change tracking capabilities

7. **Error Handling**
   - Comprehensive error capture
   - Detailed error reporting
   - Graceful failure handling
   - Debug information preservation

8. **Extensibility**
   - Plugin-style module system
   - Interface-based design
   - Custom module support
   - Framework extension capabilities

### Core Components Interaction

The core module's components interact in a structured manner:

1. **Initialization Flow**
   - `initialization.py` bootstraps the Pulumi environment
   - Loads configuration and establishes initial state
   - Sets up global metadata and Git information
   - Prepares deployment context

2. **Configuration Management**
   - `config.py` handles all configuration aspects
   - Implements layered configuration system
   - Validates configuration structures
   - Manages version information

3. **Deployment Process**
   - `deployment.py` orchestrates module deployment
   - Handles module dependencies
   - Manages deployment order
   - Tracks deployment results

4. **Resource Handling**
   - `utils.py` provides resource management helpers
   - Implements resource transformations
   - Applies metadata consistently
   - Manages resource relationships

5. **Type System**
   - `types.py` defines core data structures
   - Implements validation models
   - Provides type definitions
   - Ensures type safety

6. **Interface Definitions**
   - `interfaces.py` defines standard protocols
   - Establishes contract requirements
   - Provides base implementations
   - Ensures consistent patterns

This architectural design ensures:

- **Maintainability**: Through clear separation of concerns
- **Reliability**: Via comprehensive type checking and validation
- **Extensibility**: With modular design and clear interfaces
- **Usability**: Through consistent patterns and documentation
- **Compliance**: Via built-in security and audit capabilities


## Core Module Components

### `__init__.py`

The initialization module defines the public API and version information for the core module.

#### Key Responsibilities:

- Exposes the public interface through `__all__`
- Manages version information
- Provides module metadata
- Re-exports essential components

#### Public Exports:

```python
from pulumi.core import (
    # Configuration
    get_module_config,
    load_default_versions,
    validate_module_config,

    # Types and Interfaces
    InitializationConfig,
    ComplianceConfig,
    ModuleDeploymentResult,

    # Core Functions
    initialize_pulumi,
    setup_global_metadata,

    # Git Utilities
    collect_git_info,
    get_latest_semver_tag
)
```

#### Version Management:

```python
# Get core module version
from pulumi.core import get_version
version = get_version()

# Get module metadata
from pulumi.core import get_module_metadata
metadata = get_module_metadata()
```

### `initialization.py`

Handles the bootstrapping of Pulumi and initial configuration setup.

#### Key Features:

- Pulumi environment initialization
- Configuration loading
- Git metadata collection
- Global state setup

#### Usage Example:

```python
from pulumi.core import initialize_pulumi

# Initialize Pulumi environment
init_config = initialize_pulumi()

# Access initialization data
stack_name = init_config.stack_name
project_name = init_config.project_name
git_info = init_config.git_info
```

## Configuration Management

The configuration system implements a sophisticated layered approach to managing infrastructure configurations.

### Configuration Layers

1. **Global Defaults**
   - Base configuration layer
   - Defined in `DEFAULT_MODULE_CONFIG`
   - Provides fallback values

2. **User-Specified Sources**
   - Custom configuration files
   - Environment variables
   - Command-line arguments

3. **Stack-Specific Overrides**
   - Stack-level configurations
   - Environment-specific settings
   - Deployment context overrides

4. **Local Default Versions**
   - Module version defaults
   - Local configuration files
   - Project-specific settings

5. **Remote Versions**
   - Version information from remote sources
   - Channel-based configurations
   - Dynamic updates

### Configuration Loading Process

1. **Base Configuration**
```python
from pulumi.core.config import load_default_versions

# Load default versions with optional refresh
versions = load_default_versions(
    config=pulumi_config,
    force_refresh=False
)
```

2. **Module Configuration**
```python
from pulumi.core.config import get_module_config

# Get module-specific configuration
module_config, enabled = get_module_config(
    module_name="cert_manager",
    config=pulumi_config,
    default_versions=versions
)
```

3. **Configuration Validation**
```python
from pulumi.core.config import validate_module_config

# Validate configuration against schema
validate_module_config(
    module_name="cert_manager",
    config=module_config
)
```

### Configuration Types

#### Module Defaults
```python
ModuleDefaults = TypedDict('ModuleDefaults', {
    'enabled': bool,
    'version': Optional[str],
    'config': Dict[str, Any]
})
```

#### Compliance Configuration
```python
class ComplianceConfig:
    fisma: FismaConfig
    nist: NistConfig
    scip: ScipConfig
```

### Configuration Merging

The core module provides utilities for merging configurations from different sources:

```python
from pulumi.core.config import merge_configurations

merged_config = merge_configurations(
    base_config=default_config,
    override_config=user_config
)
```

### Version Management

#### Version Loading
```python
def load_versions_from_file(file_path: Path) -> Dict[str, Any]:
    """Load version information from JSON file."""

def load_versions_from_url(url: str) -> Dict[str, Any]:
    """Load version information from remote URL."""
```

#### Version Validation
```python
def validate_version_format(version: str) -> bool:
    """Validate semantic version format."""
```

### Configuration Caching

The core module implements configuration caching to optimize performance:

- Cache location: `/tmp/konductor`
- Cache file: `default_versions.json`
- Cache management functions
- Refresh capabilities

### Configuration Export

```python
from pulumi.core.config import export_results

# Export deployment results
export_results(
    versions=deployed_versions,
    configurations=module_configs,
    compliance=compliance_config
)
```

### Stack Outputs

The configuration system generates standardized stack outputs:

```python
from pulumi.core.config import get_stack_outputs

# Generate stack outputs
outputs = get_stack_outputs(init_config)

# Structure:
# {
#     "compliance": {...},
#     "config": {...},
#     "k8s_app_versions": {...}
# }
```

### Configuration Best Practices

1. **Validation**
   - Always validate configurations before use
   - Use type hints and Pydantic models
   - Handle validation errors gracefully

2. **Defaults**
   - Provide sensible default values
   - Document default configurations
   - Allow override of defaults

3. **Security**
   - Use Pulumi secrets for sensitive data
   - Validate security configurations
   - Implement least privilege

4. **Maintainability**
   - Keep configurations modular
   - Document configuration options
   - Use consistent naming conventions

### Error Handling

The configuration system implements comprehensive error handling:

```python
try:
    config = load_default_versions(pulumi_config)
except Exception as e:
    log.error(f"Configuration loading failed: {str(e)}")
    raise
```

### Configuration Documentation

When adding new configuration options:

1. Document the purpose and usage
2. Provide example configurations
3. Include validation requirements
4. Note any default values
5. Explain override behavior


## Deployment Orchestration

### Deployment Manager

The `DeploymentManager` class orchestrates module deployment with dependency management and error handling.

#### Key Features:

- Dynamic module loading
- Dependency resolution
- State tracking
- Error management
- Deployment results collection

#### Implementation:

```python
from pulumi.core.deployment import DeploymentManager
from pulumi.core.types import InitializationConfig

# Initialize deployment manager
deployment_manager = DeploymentManager(init_config)

# Deploy specific modules
deployment_manager.deploy_modules(["cert_manager", "kubevirt"])
```

### Module Deployment Flow

1. **Module Discovery**
```python
from pulumi.core.config import get_enabled_modules

# Get list of enabled modules
enabled_modules = get_enabled_modules(init_config.config)
```

2. **Configuration Preparation**
```python
# Module configuration retrieval and validation
module_config = init_config.config.get_object(module_name)
```

3. **Dynamic Import**
```python
# Modules are dynamically imported during deployment
deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
```

4. **Deployment Execution**
```python
# Execute module deployment
result = deploy_func(
    config=module_config,
    init_config=init_config
)
```

### Deployment Results

The `ModuleDeploymentResult` tracks deployment outcomes:

```python
class ModuleDeploymentResult(BaseModel):
    success: bool
    version: str
    resources: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

## Metadata Management

### Global Metadata System

The metadata system ensures consistent resource tagging and annotation across all deployments.

#### MetadataSingleton

Thread-safe singleton managing global metadata:

```python
from pulumi.core.metadata import (
    setup_global_metadata,
    set_global_labels,
    set_global_annotations
)

# Initialize global metadata
setup_global_metadata(init_config)

# Set specific labels/annotations
set_global_labels({"environment": "production"})
set_global_annotations({"deployment.time": "2023-01-01"})
```

### Metadata Components

1. **Labels**
   - Resource identification
   - Filtering and selection
   - Operational grouping
   - Compliance tagging

2. **Annotations**
   - Extended information
   - Deployment tracking
   - Configuration details
   - Audit trail data

### Git Metadata Integration

Automatic Git information collection and propagation:

```python
from pulumi.core.git import collect_git_info

git_info = collect_git_info()
# Returns GitInfo:
# - commit_hash
# - branch_name
# - remote_url
```

### Resource Metadata Application

The core module automatically applies metadata to resources:

```python
from pulumi.core.utils import set_resource_metadata

# Apply metadata to resource
resource_metadata = set_resource_metadata(
    metadata=existing_metadata,
    global_labels=metadata_singleton.global_labels,
    global_annotations=metadata_singleton.global_annotations
)
```

## Resource Management

### Resource Transformations

Global resource transformations ensure consistent metadata application:

```python
from pulumi.core.utils import generate_global_transformations

# Register global transformations
generate_global_transformations(
    global_labels=labels,
    global_annotations=annotations
)
```

### Resource Types

The core module supports various resource metadata types:

```python
MetadataType = Union[
    Dict[str, Any],
    ObjectMetaArgs,
    Output[Dict[str, Any]]
]
```

### Resource Handling Patterns

1. **Creation Pattern**
```python
def create_resource(name: str, metadata: MetadataType) -> Resource:
    """Create a resource with consistent metadata."""
    # Metadata is automatically transformed
    return Resource(name, metadata=metadata)
```

2. **Update Pattern**
```python
def update_resource(resource: Resource, metadata: MetadataType) -> None:
    """Update resource metadata maintaining consistency."""
    set_resource_metadata(
        metadata,
        global_labels,
        global_annotations
    )
```

### Resource Dependencies

Managing resource dependencies through Pulumi:

```python
# Resource dependency specification
resource = Resource("example",
    metadata=metadata,
    opts=pulumi.ResourceOptions(
        depends_on=[dependency]
    )
)
```

## Type Definitions and Schemas

### Core Types

1. **Initialization Configuration**
```python
class InitializationConfig(BaseModel):
    pulumi_config: pulumi.Config
    stack_name: str
    project_name: str
    default_versions: Dict[str, Any]
    git_info: GitInfo
    metadata: Dict[str, Dict[str, str]]
```

2. **Git Information**
```python
class GitInfo(BaseModel):
    commit_hash: str = 'unknown'
    branch_name: str = 'unknown'
    remote_url: str = 'unknown'
```

3. **Resource Metadata**
```python
class ResourceMetadata(BaseModel):
    created_at: datetime
    updated_at: datetime
    labels: Dict[str, str]
    annotations: Dict[str, str]
```

### Type Safety Enforcement

1. **Runtime Validation**
```python
from pydantic import ValidationError

try:
    config = InitializationConfig(**config_data)
except ValidationError as e:
    log.error(f"Configuration validation failed: {e}")
    raise
```

2. **Type Checking**
```python
# Type hints for function arguments
def process_config(
    config: InitializationConfig,
    metadata: ResourceMetadata
) -> ModuleDeploymentResult:
    ...
```

### Interface Definitions

Core interfaces ensuring consistent implementation:

```python
class ModuleInterface(Protocol):
    def validate_config(self, config: Dict[str, Any]) -> List[str]: ...
    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult: ...
    def get_dependencies(self) -> List[str]: ...
```

### Compliance Types

Structured compliance configuration types:

```python
class ComplianceConfig:
    fisma: FismaConfig
    nist: NistConfig
    scip: ScipConfig
```

### Type Utilities

Helper functions for type management:

```python
def validate_url(url: str) -> bool:
    """Validate URL format."""

def sanitize_git_info(git_info: Dict[str, str]) -> Dict[str, str]:
    """Sanitize git information for use in tags."""
```

## Usage Guidelines

### Core Module Integration

#### Basic Implementation

1. **Project Entry Point**
```python
from pulumi.core import (
    initialize_pulumi,
    setup_global_metadata,
    get_enabled_modules,
    DeploymentManager
)

def main() -> None:
    try:
        # Initialize Pulumi
        init_config = initialize_pulumi()

        # Setup metadata
        setup_global_metadata(init_config)

        # Get enabled modules
        modules = get_enabled_modules(init_config.config)

        # Deploy modules
        deployment_manager = DeploymentManager(init_config)
        deployment_manager.deploy_modules(modules)

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        sys.exit(1)
```

#### Custom Module Development

1. **Module Structure**
```plaintext
modules/custom_module/
├── __init__.py
├── config.py
├── deploy.py
├── types.py
└── utils.py
```

2. **Deployment Implementation**
```python
# modules/custom_module/deploy.py
from pulumi.core import (
    ModuleDeploymentResult,
    InitializationConfig
)

def deploy(
    config: dict,
    init_config: InitializationConfig
) -> ModuleDeploymentResult:
    """Deploy custom module resources."""
    try:
        # Implementation
        return ModuleDeploymentResult(
            success=True,
            version="1.0.0",
            resources=["resource-1"]
        )
    except Exception as e:
        return ModuleDeploymentResult(
            success=False,
            version="1.0.0",
            errors=[str(e)]
        )
```

### Configuration Patterns

#### Stack Configuration

```yaml
# Pulumi.<stack>.yaml
config:
  konductor:
    modules:
      custom_module:
        enabled: true
        version: "1.0.0"
        config:
          key: "value"

    compliance:
      fisma:
        enabled: true
        level: "moderate"
```

#### Module Configuration

```python
# modules/custom_module/config.py
from pydantic import BaseModel

class ModuleConfig(BaseModel):
    enabled: bool = False
    version: str
    settings: Dict[str, Any] = {}

def validate_config(config: Dict[str, Any]) -> ModuleConfig:
    return ModuleConfig(**config)
```

## Best Practices

### Code Organization

1. **Module Structure**
   - Keep related functionality together
   - Use clear file naming
   - Maintain consistent organization
   - Document module relationships

2. **Type Safety**
   - Use type hints extensively
   - Implement validation models
   - Define clear interfaces
   - Document type requirements

3. **Error Handling**
   - Implement comprehensive error handling
   - Provide meaningful error messages
   - Log errors appropriately
   - Maintain error context

4. **Configuration Management**
   - Use typed configurations
   - Implement validation
   - Provide defaults
   - Document options

### Resource Management

1. **Resource Creation**
   - Use consistent patterns
   - Apply appropriate metadata
   - Handle dependencies
   - Implement error handling

2. **Metadata Application**
   - Use global metadata utilities
   - Maintain consistency
   - Document special cases
   - Validate metadata

### Testing Practices

1. **Unit Testing**
```python
import pytest
from pulumi.core import validate_module_config

def test_config_validation():
    config = {
        "enabled": True,
        "version": "1.0.0"
    }
    result = validate_module_config("test_module", config)
    assert result is None
```

2. **Integration Testing**
```python
def test_module_deployment(pulumi_test):
    """Test module deployment with mocked Pulumi."""
    with pulumi_test:
        result = deploy(test_config, init_config)
        assert result.success
```

## Development Guidelines

### Code Style

1. **Python Standards**
   - Follow PEP 8
   - Use consistent naming
   - Document code properly
   - Maintain clean structure

2. **Type Annotations**
   - Use proper type hints
   - Document type constraints
   - Validate types runtime
   - Handle type errors

### Documentation

1. **Code Documentation**
   - Write clear docstrings
   - Document parameters
   - Explain return values
   - Provide examples

2. **Module Documentation**
   - Maintain README files
   - Document configurations
   - Provide usage examples
   - Update regularly

### Contribution Process

1. **Code Submission**
   - Follow coding standards
   - Include tests
   - Update documentation
   - Submit pull requests

2. **Review Process**
   - Code review guidelines
   - Testing requirements
   - Documentation review
   - Approval process

## Testing and Validation

### Unit Testing

1. **Test Structure**
```python
# tests/core/test_config.py
def test_load_default_versions():
    """Test version loading functionality."""

def test_validate_module_config():
    """Test configuration validation."""
```

2. **Mocking**
```python
@pytest.fixture
def mock_git_info(mocker):
    """Mock Git information collection."""
    return mocker.patch('pulumi.core.git.collect_git_info')
```

### Integration Testing

1. **Pulumi Testing**
```python
def test_deployment_flow():
    """Test end-to-end deployment."""
```

2. **Resource Testing**
```python
def test_resource_creation():
    """Test resource creation with metadata."""
```

## Security Considerations

### Compliance Integration

1. **Security Controls**
   - Implement NIST controls
   - Follow FISMA requirements
   - Enable audit logging
   - Enforce policies

2. **Compliance Validation**
   - Validate configurations
   - Check requirements
   - Generate reports
   - Track compliance

### Secret Management

1. **Secure Configuration**
   - Use Pulumi secrets
   - Encrypt sensitive data
   - Manage access control
   - Rotate credentials

## Related Documentation

- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Guide](../developer_guide/pulumi-python.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)
- [TypedDict Reference](../reference/TypedDict.md)

## Additional Resources

### Community Support

- Discord: [ContainerCraft Community](https://discord.gg/Jb5jgDCksX)
- GitHub: [Issues](https://github.com/containercraft/konductor/issues)
- Documentation: [User Guide](../user_guide/README.md)

### Version Information

- Get current version: `get_version()`
- Check compatibility: [Compatibility Matrix](../reference/compatibility.md)
- Release notes: [Changelog](../CHANGELOG.md)

## Conclusion

The Konductor Core Module provides a robust foundation for infrastructure deployment, offering comprehensive features for configuration management, deployment orchestration, and resource handling. By following these guidelines and best practices, teams can effectively utilize the core module to build and maintain their infrastructure platform.
