# Konductor Core Module Documentation

## Introduction

The **Konductor Core Module** is the foundational framework for the Konductor Infrastructure as Code (IaC) platform built with Pulumi and Python. It provides a robust, type-safe, and maintainable architecture that enables development teams to work independently while ensuring consistency, compliance, and best practices across all infrastructure deployments.

This documentation is intended for developers of all levels, DevOps practitioners, module maintainers, and contributors. It serves as a comprehensive guide to understanding, utilizing, and extending the core module effectively and confidently.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
   - [Directory Structure](#directory-structure)
   - [Design Philosophy](#design-philosophy)
2. [Core Module Components](#core-module-components)
   - [`__init__.py`](#__init__py)
   - [`config.py`](#configpy)
   - [`deployment.py`](#deploymentpy)
   - [`metadata.py`](#metadatapy)
   - [`resource_helpers.py`](#resource_helperspy)
   - [`types.py`](#typespy)
   - [`utils.py`](#utilspy)
3. [Configuration Management](#configuration-management)
   - [Complexity Rationale](#complexity-rationale)
   - [Configuration Layers](#configuration-layers)
4. [Deployment Orchestration](#deployment-orchestration)
5. [Metadata and Tagging](#metadata-and-tagging)
6. [Resource Management](#resource-management)
7. [Type Definitions and Schemas](#type-definitions-and-schemas)
8. [Utility Functions](#utility-functions)
9. [Usage Guidelines](#usage-guidelines)
   - [When to Use the Core Module](#when-to-use-the-core-module)
   - [Extending the Core Module](#extending-the-core-module)
10. [Best Practices](#best-practices)
11. [Development Guidelines](#development-guidelines)
12. [Contribution Guidelines](#contribution-guidelines)
13. [Conclusion](#conclusion)
14. [Related Documentation](#related-documentation)

---

## Architecture Overview

### Directory Structure

The core module is organized to promote clarity, maintainability, and ease of use:

```
core/
├── __init__.py           # Module initialization and public API exports
├── config.py             # Advanced configuration management system
├── deployment.py         # Deployment orchestration and lifecycle management
├── metadata.py           # Global metadata and tagging utilities
├── resource_helpers.py   # Common resource creation and management functions
├── types.py              # Shared type definitions and schemas
└── utils.py              # General utility functions
```

### Design Philosophy

The core module is designed with the following principles:

1. **Separation of Concerns**: Each component addresses a specific aspect of the infrastructure management process.
2. **Type Safety**: Comprehensive use of type annotations and `TypedDict` to ensure reliability and prevent runtime errors.
3. **Configuration Isolation**: Enables modules to define and manage their own configurations independently.
4. **Resource Abstraction**: Provides reusable patterns for resource creation to promote consistency.
5. **Compliance Integration**: Incorporates security and compliance requirements seamlessly.
6. **Team Autonomy**: Allows teams to work independently without impacting other modules or the core functionality.

---

## Core Module Components

### `__init__.py`

**Purpose**: Initializes the core module and exposes its public API.

**Key Responsibilities**:

- Import and expose essential classes and functions.
- Define `__all__` to manage the public interface.
- Provide module-level docstrings that describe the module's purpose and usage.

**Example**:

```python
"""
Core module initialization and public API exposure.
"""

from .config import ConfigurationManager
from .deployment import DeploymentManager
from .metadata import MetadataManager
from .resource_helpers import ResourceManager
from .types import BaseConfig, ResourceConfig
from .utils import merge_configurations

__all__ = [
    "ConfigurationManager",
    "DeploymentManager",
    "MetadataManager",
    "ResourceManager",
    "BaseConfig",
    "ResourceConfig",
    "merge_configurations",
]
```

### `config.py`

**Purpose**: Manages complex configuration hierarchies across the platform.

**Key Responsibilities**:

- Merge configurations from various sources (defaults, environment variables, user inputs).
- Validate configurations against predefined schemas.
- Provide configuration isolation for individual modules.
- Support environment-specific settings.

**Example**:

```python
from typing import Dict, Any

class ConfigurationManager:
    """
    Manages layered configurations for modules.

    Configuration precedence:
    1. Global defaults
    2. Environment variables
    3. Stack-specific overrides
    4. User-provided configurations
    5. Module-specific settings
    """

    def __init__(self):
        self.global_defaults = self.load_global_defaults()

    def get_config(self, module_name: str) -> Dict[str, Any]:
        """Retrieve the merged configuration for a module."""
        module_defaults = self.load_module_defaults(module_name)
        user_config = self.load_user_config(module_name)
        return self.merge_configurations(
            self.global_defaults,
            module_defaults,
            user_config
        )
```

### `deployment.py`

**Purpose**: Orchestrates the deployment process and manages resource lifecycles.

**Key Responsibilities**:

- Discover and load modules dynamically.
- Resolve resource dependencies and creation order.
- Handle errors and implement rollback mechanisms.
- Interface with Pulumi's state management.

**Example**:

```python
from typing import List

class DeploymentManager:
    """
    Orchestrates module deployments.

    Responsibilities:
    - Module discovery and initialization
    - Dependency resolution
    - Resource lifecycle management
    - Error handling and rollback
    - State synchronization with Pulumi
    """

    def deploy(self, modules: List[str]) -> None:
        """Deploy specified modules."""
        for module_name in modules:
            self.initialize_module(module_name)
        self.resolve_dependencies()
        self.execute_deployment()
```

### `metadata.py`

**Purpose**: Manages global metadata and resource tagging.

**Key Responsibilities**:

- Generate and apply standardized tags for compliance.
- Integrate Git metadata (e.g., commit hashes) for traceability.
- Provide utilities for consistent resource metadata application.

**Example**:

```python
from typing import Dict

class MetadataManager:
    """
    Handles global metadata and tagging for resources.

    - Generates compliance tags
    - Integrates version control metadata
    - Provides methods to apply metadata to resources
    """

    def get_standard_tags(self) -> Dict[str, str]:
        """Return a dictionary of standard tags to apply to resources."""
        return {
            "Project": "Konductor",
            "ManagedBy": "Pulumi",
            "GitCommit": self.get_git_commit_hash(),
        }

    def apply_tags(self, resource, tags: Dict[str, str]) -> None:
        """Apply tags to a given resource."""
        resource.tags.apply(lambda existing_tags: {**existing_tags, **tags})
```

### `resource_helpers.py`

**Purpose**: Provides common patterns and utilities for resource creation.

**Key Responsibilities**:

- Simplify resource creation with standardized methods.
- Ensure consistent application of metadata and compliance controls.
- Manage resource dependencies and error handling.

**Example**:

```python
from typing import Dict, Any
import pulumi

class ResourceManager:
    """
    Offers helper methods for resource creation.

    - Standardizes resource instantiation
    - Applies metadata and compliance tags
    - Manages dependencies and error handling
    """

    def create_resource(
        self,
        resource_type: Any,
        name: str,
        args: Dict[str, Any],
        opts: pulumi.ResourceOptions = None
    ) -> pulumi.Resource:
        """Create a resource with standardized settings."""
        metadata_manager = MetadataManager()
        standard_tags = metadata_manager.get_standard_tags()
        args['tags'] = {**args.get('tags', {}), **standard_tags}
        return resource_type(name, **args, opts=opts)
```

### `types.py`

**Purpose**: Defines shared type definitions and data schemas.

**Key Responsibilities**:

- Provide base configuration types using `TypedDict` or Pydantic models.
- Ensure consistent data structures across modules.
- Facilitate type checking and validation.

**Example**:

```python
from typing import TypedDict, Optional, Dict, Any

class BaseConfig(TypedDict):
    """Base configuration structure for modules."""
    enabled: bool
    version: Optional[str]
    parameters: Dict[str, Any]
```

### `utils.py`

**Purpose**: Contains general utility functions used across the core module.

**Key Responsibilities**:

- Provide common utility functions (e.g., configuration merging, string manipulation).
- Enhance performance and code reusability.
- Support other core components with shared functionalities.

**Example**:

```python
from typing import Dict, Any

def merge_configurations(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries into one."""
    result = {}
    for config in configs:
        result.update(config)
    return result
```

---

## Configuration Management

### Complexity Rationale

The configuration system is intentionally designed to handle complex scenarios to support:

- **Team Autonomy**: Allowing different teams to define their own configurations without impacting others.
- **Environment Variability**: Managing configurations across multiple environments (development, staging, production).
- **Compliance Requirements**: Enforcing organizational policies and standards centrally.
- **Scalability**: Accommodating a growing number of modules and configurations efficiently.

### Configuration Layers

Configurations are merged and resolved in the following order of precedence:

1. **Global Defaults**: Baseline settings applicable to all modules.
2. **Environment Variables**: Settings specific to the deployment environment.
3. **Stack-Specific Overrides**: Customizations for specific Pulumi stacks.
4. **User-Provided Configurations**: Inputs provided by users or module maintainers.
5. **Module-Specific Settings**: Configurations defined within individual modules.

---

## Deployment Orchestration

The `DeploymentManager` class in `deployment.py` handles the orchestration of module deployments:

- **Module Discovery**: Automatically identifies modules to deploy based on the directory structure or configuration.
- **Initialization**: Loads module configurations and initializes resources.
- **Dependency Resolution**: Determines the order of resource creation based on dependencies.
- **Execution**: Coordinates the creation, updating, or deletion of resources as defined in the code.
- **Error Handling**: Implements mechanisms to catch and handle errors gracefully, including rollbacks if necessary.

---

## Metadata and Tagging

Consistent metadata and tagging are crucial for:

- **Compliance**: Meeting organizational and regulatory requirements.
- **Traceability**: Tracking resource changes and deployments.
- **Management**: Facilitating resource identification and categorization.

The `MetadataManager` provides methods to generate and apply standard tags to resources automatically.

---

## Resource Management

The `ResourceManager` in `resource_helpers.py` simplifies resource creation by:

- **Applying Standard Configurations**: Ensuring resources are created with necessary settings.
- **Managing Metadata**: Automatically adding standard tags and labels.
- **Handling Dependencies**: Allowing explicit specification of resource dependencies.
- **Error Handling**: Providing consistent error messages and handling strategies.

---

## Type Definitions and Schemas

Using `TypedDict` and type annotations:

- **Enhances Type Safety**: Catches errors during development rather than at runtime.
- **Improves Readability**: Makes code self-documenting and easier to understand.
- **Assists IDEs**: Provides better auto-completion and linting support.
- **Facilitates Validation**: Ensures data structures conform to expected formats.

---

## Utility Functions

Utility functions in `utils.py` support the core module by:

- **Simplifying Common Tasks**: Providing reusable functions for tasks like configuration merging.
- **Enhancing Performance**: Implementing efficient algorithms where applicable.
- **Promoting Code Reuse**: Reducing duplication and promoting DRY principles.

---

## Usage Guidelines

### When to Use the Core Module

Use the core module when you need to:

- **Implement Shared Functionality**: Features or patterns used across multiple modules.
- **Enforce Standards**: Organizational policies, compliance requirements, or best practices.
- **Promote Consistency**: Ensure uniform behavior and configurations across resources.
- **Reduce Duplication**: Avoid repeating code by centralizing common logic.

### Extending the Core Module

When extending the core module:

- **Assess Necessity**: Determine if the functionality is broadly applicable.
- **Maintain Separation of Concerns**: Keep functionalities modular and focused.
- **Ensure Backward Compatibility**: Avoid breaking existing implementations.
- **Document Thoroughly**: Update documentation and provide examples for new features.

---

## Best Practices

- **Type Annotations**: Use type hints throughout the code for clarity and error prevention.
- **Documentation**: Provide comprehensive docstrings and inline comments.
- **Compliance Adherence**: Utilize the core module's compliance features to meet requirements.
- **Modular Design**: Keep code organized and modular for maintainability.
- **Testing**: Write unit and integration tests to ensure code reliability.
- **DRY Principle**: Avoid code duplication by abstracting common functionalities.

---

## Development Guidelines

- **Code Style**: Follow the project's coding standards as outlined in the [Pulumi Python Development Guide](../developer_guide/pulumi-python.md).
- **Type Safety**: Enforce strict type checking using tools like Pyright.
- **Error Handling**: Implement robust error handling and provide meaningful messages.
- **Version Control**: Use meaningful commit messages and follow branching strategies.
- **Continuous Integration**: Integrate automated testing and linting in the development workflow.

---

## Contribution Guidelines

- **Proposing Changes**:

  - Discuss proposed changes with the maintainers before implementation.
  - Ensure alignment with the project's goals and standards.

- **Implementation**:

  - Write clean, type-safe code.
  - Include unit tests and documentation updates.
  - Follow the project's style and contribution guidelines.

- **Pull Requests**:

  - Provide detailed descriptions of changes.
  - Reference related issues or discussions.
  - Be responsive to feedback during the review process.

---

## Conclusion

The Konductor Core Module is a vital component of the platform, enabling efficient, consistent, and compliant infrastructure deployments. By understanding its architecture and following the guidelines provided, developers can effectively utilize and contribute to the core module, fostering a collaborative and high-quality development environment.

---

## Related Documentation

- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Development Guide](../developer_guide/pulumi-python.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)
- [TypedDict Reference Guide](../reference/TypedDict.md)
