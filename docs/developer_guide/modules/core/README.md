# Konductor Core Module Documentation

## Introduction

The **Konductor Core Module** serves as the foundational framework for Infrastructure as Code (IaC) using Pulumi and Python. It provides a robust, type-safe, and maintainable architecture that enables teams to work independently while ensuring consistency and compliance across infrastructure deployments. By abstracting common IaC patterns, the core module makes your codebase more DRY (Don't Repeat Yourself), reusable, and dynamic.

This documentation is intended for a wide audience, including junior, senior, and principal developers, DevOps practitioners, executive leadership, and the open-source community.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Module Components](#core-module-components)
  - [Directory Structure](#directory-structure)
  - [Design Philosophy](#design-philosophy)
- [Detailed Component Descriptions](#detailed-component-descriptions)
  - [`__init__.py`](#__init__py)
  - [`config.py`](#configpy)
    - [Why Is Configuration Complex?](#why-is-configuration-complex)
  - [`deployment.py`](#deploymentpy)
  - [`metadata.py`](#metadatapy)
  - [`resource_helpers.py`](#resource_helperspy)
  - [`types.py`](#typespy)
  - [`utils.py`](#utilspy)
- [Kubernetes Module Centralized Version Control](#kubernetes-module-centralized-version-control)
- [Main Entry Point `__main__.py`](#main-entry-point-__main__py)
- [When to Use Core Module vs. Module-Specific Code](#when-to-use-core-module-vs-module-specific-code)
- [Best Practices](#best-practices)
- [Development Guidelines](#development-guidelines)
- [Conclusion](#conclusion)

## Architecture Overview

### Directory Structure

The core module is organized as follows:

```
pulumi/core/
├── __init__.py           # Module initialization and exports
├── config.py             # Advanced configuration management system
├── deployment.py         # Deployment orchestration and lifecycle management
├── metadata.py           # Global metadata and tagging utilities
├── resource_helpers.py   # Common resource creation and management functions
├── types.py              # Shared type definitions and schemas
└── utils.py              # General utility functions
```

### Design Philosophy

The core module implements several key principles:

1. **Separation of Concerns**: Each component has a single, well-defined responsibility.
2. **Type Safety**: Comprehensive type checking throughout the codebase to prevent runtime errors.
3. **Configuration Isolation**: Modules can define their own configuration schemas independently.
4. **Resource Abstraction**: Centralizes common resource patterns for consistency and reuse.
5. **Compliance Integration**: Built-in support for security and compliance requirements.
6. **Team Independence**: Enables different teams to maintain independent configurations without affecting others.

## Detailed Component Descriptions

### `__init__.py`

This file initializes the core module and exports essential classes and functions for external use. It serves as the entry point for the module, making it easier for other parts of the program to import and utilize core functionalities.

### `config.py`

**Purpose**: Manages the complex configuration hierarchy used across the entire IaC codebase.

**Key Features**:

- **Layered Configuration**: Merges configurations from global defaults, stack-specific settings, environment variables, and module-specific overrides.
- **Validation**: Ensures that configurations meet predefined schemas and compliance requirements.
- **Flexibility**: Supports multiple deployment environments and scenarios.
- **Team Independence**: Allows each module team to maintain independent configuration specifications.

#### Why Is Configuration Complex?

The configuration system is intentionally complex to accommodate:

- **Multi-Team Development**: Enables teams to define their own configuration schemas without impacting others.
- **Version Control**: Each module maintains its own application versioning, allowing for independent updates.
- **Compliance Requirements**: Centralized validation enforces security and compliance standards.
- **Environment-Specific Configurations**: Supports varying configurations across many teams with their own development, staging, and production environments.
- **Default Value Management**: Provides a mechanism for default settings that can be overridden as needed.

**Example**:

```python
class ConfigurationManager:
    """
    Manages the complex configuration hierarchy:
    1. Default values
    2. Stack-specific overrides
    3. Environment variables
    4. User-provided configurations
    5. Module-specific settings
    """

    def get_config(self, module_name: str) -> Dict[str, Any]:
        # Logic to merge configurations
        pass
```

### `deployment.py`

**Purpose**: Orchestrates the deployment process, managing the lifecycle of resources and modules.

**Key Features**:

- **Automatic Module Discovery**: Dynamically loads and initializes modules from the `pulumi/modules/` directory.
- **Dependency Resolution**: Ensures resources are created in the correct order based on dependencies.
- **Parallel Deployment Capabilities**: Optimizes deployment time by parallelizing independent resource creations.
- **Comprehensive Error Handling**: Provides robust mechanisms to handle failures and rollbacks.
- **State Management**: Interfaces with Pulumi's state management to track resource states.

**Example**:

```python
class DeploymentManager:
    """
    Manages the deployment lifecycle:
    - Module discovery and loading
    - Dependency resolution
    - Resource creation ordering
    - Error handling and recovery
    - State management
    """

    def deploy(self):
        # Logic to orchestrate deployment
        pass
```

### `metadata.py`

**Purpose**: Handles global metadata and labeling for resources.

**Key Features**:

- **Compliance Labels**: Automatically generates and distributes required compliance and audit tags to resources.
- **Git Information Integration**: Incorporates Git metadata (e.g., commit hashes) into resource tags for traceability.
- **Resource Tagging Standards**: Enforces consistent tagging across all modules leaving module maintainers free to implement provider specific tagging implementations.
- **Audit Trail Maintenance**: Facilitates auditing by returning reportable metadata.

**Example**:

```python
class MetadataManager:
    """
    Manages global metadata:
    - Compliance labels
    - Git information
    - Resource tagging
    - Audit trail
    """

    def get_metadata(self) -> Dict[str, str]:
        # Returns standardized metadata for resources
        pass
```

### `resource_helpers.py`

**Purpose**: Centralizes common resource creation patterns and utilities.

**Key Features**:

- **Consistent Metadata Application**: Ensures all resources have the necessary metadata and tags.
- **Standardized Error Handling**: Provides consistent mechanisms for handling resource creation errors.
- **Resource Dependencies**: Simplifies the management of resource dependencies and ordering.
- **Cleanup Procedures**: Implements standardized procedures for resource deletion and cleanup.

**Example**:

```python
class ResourceManager:
    """
    Provides standardized resource creation patterns:
    - Consistent metadata application
    - Error handling
    - Resource dependencies
    - Cleanup procedures
    """

    def create_resource(self, config: Dict[str, Any]) -> pulumi.Resource:
        # Logic to create a resource with standardized settings
        pass
```

### `types.py`

**Purpose**: Defines shared type definitions and schemas used across modules.

**Key Features**:

- **Type Definitions**: Provides base classes and type hints for configurations and resources.
- **Schema Validation**: Ensures that configurations adhere to expected structures.
- **Reusability**: Facilitates consistent typing across different modules.

**Example**:

```python
from typing import TypedDict

class BaseConfig(TypedDict):
    """Base configuration structure for all modules."""
    enabled: bool
    version: str
    parameters: Dict[str, Any]

class ResourceConfig(TypedDict):
    """Standard resource configuration structure."""
    name: str
    type: str
    metadata: Dict[str, Any]
```

### `utils.py`

**Purpose**: Contains general utility functions that support other components.

**Key Features**:

- **Common Utilities**: Functions for tasks like merging configurations, handling strings, etc.
- **Helper Functions**: Small, reusable functions that are used across multiple modules.
- **Performance Optimization**: Includes functions that enhance performance and efficiency.

**Example**:

```python
def merge_configurations(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merges multiple configuration dictionaries into one."""
    # Logic to merge dictionaries
    pass
```

## Kubernetes Module Centralized Version Control

**Purpose**: The Kubernetes module centralizes version control to ensure consistency and reliability across all deployments.

**Reasons for Centralization**:

- **Consistency**: Guarantees that all modules and environments can opt in to a centralized, common version control system.
- **Simplified Upgrades**: Streamlines the process of maintaining component versions at scale.
- **Compliance and Security**: Ensures that only approved and secure versions are used, adhering to organizational policies.
- **Reduced Conflicts**: Minimizes the risk of version incompatibilities between different modules.

By centralizing version control in the core module, teams can focus on their specific functionalities without worrying about underlying Kubernetes version discrepancies.

## Main Entry Point `__main__.py`

The `__main__.py` file serves as the simple entry point for the Pulumi program. It is designed to be straightforward, allowing different module teams to maintain independent configuration specifications without interference.

**Key Features**:

- **Simplified Orchestration**: Delegates the deployment process to the `DeploymentManager` in `deployment.py`.
- **Team Autonomy**: Each team's module can be developed and deployed independently.
- **Preventing Cross-Team Interference**: Changes in one module's deployment do not affect others.

**Example**:

```python
import pulumi
from core.deployment import DeploymentManager

# Initialize the deployment manager
deployment_manager = DeploymentManager()

# Execute the deployment process
deployment_manager.deploy()
```

## When to Use Core Module vs. Module-Specific Code

### Core Module Code

**Use the core module when**:

- The functionality is **used by multiple modules**.
- It **implements organizational standards** or compliance requirements.
- It **provides common resource patterns** that promote consistency.
- You need to **abstract repetitive code** to make it DRY.

**Example**:

```python
# Core module - get module configuration
def get_module_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Returns the module configuration."""
    pass
```

### Module-Specific Code

**Keep code in individual modules when**:

- It's **specific to one module's functionality**.
- It implements **module-specific business logic**.
- It handles **module-specific resource types** not used elsewhere.
- It doesn't need to be shared across modules.

**Example**:

```python
# AWS module - reusable but only within AWS module resource patterns
def create_compliant_s3_bucket(name: str, config: Dict[str, Any]) -> s3.Bucket:
    """Creates an S3 bucket with standard compliance controls."""
    # Logic to create the bucket
    pass
```

## Best Practices

- **Maintain Type Safety**: Use type hints and `TypedDict` to prevent runtime errors.
- **Follow the DRY Principle**: Abstract common code into the core module to avoid duplication.
- **Isolate Configurations**: Keep module configurations independent to prevent conflicts.
- **Document Thoroughly**: Provide clear docstrings and comments for all functions and classes.
- **Implement Comprehensive Error Handling**: Use custom exceptions and handle errors gracefully.
- **Use Centralized Metadata**: Apply consistent tagging and labeling using the `metadata.py` utilities.
- **Adhere to Compliance Standards**: Leverage the core module's compliance features to meet organizational policies.

## Development Guidelines

- **Adding New Core Features**:

  - **Evaluate the Need**:
    - Is the functionality used by multiple modules?
    - Does it align with organizational standards?
    - Should it be centralized for consistency?

  - **Design**:
    - Create clear type definitions.
    - Plan for error handling and edge cases.
    - Consider backward compatibility.

  - **Implementation**:
    - Write type-safe, clean code.
    - Add comprehensive unit tests.
    - Document the new feature thoroughly.

- **Testing**:

  - **Unit Tests**: Test individual components for correctness and type safety.
  - **Integration Tests**: Verify interactions between components and modules.
  - **Compliance Tests**: Ensure new features meet security and compliance requirements.

- **Contributing**:

  - **Propose Changes**: Discuss your ideas with maintainers before implementation.
  - **Follow Code Standards**: Adhere to the project's coding guidelines.
  - **Submit Pull Requests**: Provide detailed descriptions and await code reviews.
