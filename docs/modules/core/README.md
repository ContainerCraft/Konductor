# Konductor Core Module Documentation

## Introduction

The **Konductor Core Module** is the foundational framework for the Konductor Infrastructure as Code (IaC) platform built with Pulumi and Python. It provides core functionalities such as configuration management, deployment orchestration, resource management, and compliance controls, enabling development teams to build and deploy infrastructure in a consistent, secure, and maintainable manner.

This documentation is intended for developers, DevOps practitioners, module maintainers, and contributors. It serves as a comprehensive guide to understanding, utilizing, and extending the core module effectively and confidently.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
   - [Directory Structure](#directory-structure)
   - [Design Philosophy](#design-philosophy)
2. [Core Module Components](#core-module-components)
   - [`__init__.py`](#initpy)
   - [`initialization.py`](#initializationpy)
   - [`config.py`](#configpy)
   - [`deployment.py`](#deploymentpy)
   - [`metadata.py`](#metadatapy)
   - [`git.py`](#gitpy)
   - [`types.py`](#typespy)
   - [`interfaces.py`](#interfacespy)
   - [`resource_helpers.py`](#resource_helperspy)
   - [`utils.py`](#utilspy)
3. [Configuration Management](#configuration-management)
   - [Layers of Configuration](#layers-of-configuration)
   - [Default Module Configuration](#default-module-configuration)
4. [Initialization Flow](#initialization-flow)
5. [Deployment Orchestration](#deployment-orchestration)
6. [Metadata and Tagging](#metadata-and-tagging)
7. [Resource Management Helpers](#resource-management-helpers)
8. [Type Definitions and Schemas](#type-definitions-and-schemas)
9. [Git Utilities](#git-utilities)
10. [Interfaces and Protocols](#interfaces-and-protocols)
11. [Utility Functions](#utility-functions)
12. [Usage Guidelines](#usage-guidelines)
    - [When to Use the Core Module](#when-to-use-the-core-module)
    - [Extending the Core Module](#extending-the-core-module)
13. [Best Practices](#best-practices)
14. [Development Guidelines](#development-guidelines)
15. [Contribution Guidelines](#contribution-guidelines)
16. [Conclusion](#conclusion)
17. [Related Documentation](#related-documentation)

---

## Architecture Overview

### Directory Structure

The core module is organized to promote clarity, maintainability, and ease of use:

```
core/
├── __init__.py             # Module initialization and public API exports
├── initialization.py       # Pulumi initialization and configuration loading
├── config.py               # Advanced configuration management
├── deployment.py           # Deployment orchestration and module management
├── metadata.py             # Global metadata and tagging utilities
├── git.py                  # Git utilities for repository information
├── types.py                # Shared type definitions and data models
├── interfaces.py           # Protocols and interfaces definitions
└── utils.py                # General utility functions
```

### Design Philosophy

The core module is designed with the following principles:

1. **Separation of Concerns**: Each component addresses a specific aspect of the infrastructure management process.
2. **Type Safety**: Comprehensive use of type hints, Pydantic models, and `TypedDict` to ensure reliability and prevent runtime errors.
3. **Configuration Isolation**: Enables modules to define and manage their own configurations independently.
4. **Resource Abstraction**: Provides reusable patterns for resource creation to promote consistency.
5. **Compliance Integration**: Incorporates security and compliance requirements seamlessly.
6. **Modular and Extensible Design**: Facilitates adding new functionalities without affecting existing components.

---

## Core Module Components

### `__init__.py`

**Purpose**: Initializes the core module and exposes its public API.

**Key Responsibilities**:

- Import and expose essential classes, functions, and types.
- Define `__all__` to manage the public interface.
- Provide module-level docstrings that describe the module's purpose and usage.

**Overview**:

The `__init__.py` file re-exports functions and classes from submodules to provide a clean and organized public API.

**Example**:

```python
"""
Konductor Core Module

This module provides the core functionality for the Konductor Infrastructure as Code platform.
It handles configuration management, deployment orchestration, resource management,
and compliance controls.

Key Components:
- Configuration Management
- Deployment Orchestration
- Metadata Management
- Type Definitions

Usage:
    from modules.core import (
        initialize_pulumi,
        get_module_config,
        load_default_versions,
        ComplianceConfig,
        InitializationConfig,
        # ... other imports as needed
    )
"""

__version__ = "0.0.1"
__author__ = "ContainerCraft Konductor Maintainers"

# Type exports
from .types import (
    ComplianceConfig,
    InitializationConfig,
    ModuleBase,
    ModuleDefaults,
    FismaConfig,
    NistConfig,
    ScipConfig,
    StackOutputs,
    # ... other types
)

# Interfaces
from .interfaces import (
    DeploymentContext,
    ModuleInterface,
    ModuleDeploymentResult,
    ResourceMetadata,
    # ... other interfaces
)

# Configuration management
from .config import (
    get_module_config,
    load_default_versions,
    export_results,
    validate_module_config,
    initialize_config,
    merge_configurations,
    DEFAULT_MODULE_CONFIG,
    get_stack_outputs,
    # ... other config functions
)

# Metadata management
from .metadata import (
    setup_global_metadata,
    set_global_labels,
    set_global_annotations,
    # ... other metadata functions
)

# Git utilities
from .git import (
    collect_git_info,
    get_latest_semver_tag,
    get_remote_url,
    sanitize_git_info,
    extract_repo_name,
    # ... other git functions
)

# Utility functions
from .utils import (
    set_resource_metadata,
    generate_global_transformations,
    # ... other utility functions
)

# Initialization
from .initialization import initialize_pulumi

# Public API
__all__ = [
    "__version__",
    "__author__",
    # Types
    "ComplianceConfig",
    "InitializationConfig",
    "ModuleBase",
    "ModuleDefaults",
    "FismaConfig",
    "NistConfig",
    "ScipConfig",
    "StackOutputs",
    # Interfaces
    "DeploymentContext",
    "ModuleInterface",
    "ModuleDeploymentResult",
    "ResourceMetadata",
    # Configuration
    "get_module_config",
    "load_default_versions",
    "export_results",
    "validate_module_config",
    "initialize_config",
    "merge_configurations",
    "DEFAULT_MODULE_CONFIG",
    "get_stack_outputs",
    # Deployment
    "initialize_pulumi",
    # Metadata
    "setup_global_metadata",
    "set_global_labels",
    "set_global_annotations",
    # Git Utilities
    "collect_git_info",
    "get_latest_semver_tag",
    "get_remote_url",
    "sanitize_git_info",
    "extract_repo_name",
    # Utilities
    "set_resource_metadata",
    "generate_global_transformations",
    # ... other exports
]
```

### `initialization.py`

**Purpose**: Handles the initialization of Pulumi and the loading of configurations.

**Key Responsibilities**:

- Load Pulumi stack and project information.
- Collect Git repository metadata.
- Initialize the `InitializationConfig` object with all necessary initialization data.

**Overview**:

The `initialize_pulumi` function centralizes the initialization logic, ensuring that all required configurations and metadata are loaded before deployment begins.

**Example**:

```python
import pulumi
from pulumi import Config, get_stack, get_project, log
from modules.core.types import InitializationConfig
from modules.core.git import collect_git_info

def initialize_pulumi() -> InitializationConfig:
    """
    Initializes Pulumi and loads the configuration.

    Returns:
        InitializationConfig: The initialization configuration object.
    """
    try:
        # Load Pulumi configuration
        pulumi_config = Config()
        stack_name = get_stack()
        project_name = get_project()

        # Collect Git metadata
        git_info = collect_git_info()
        log.info(
            f"Git Info: commit_hash='{git_info.commit_hash}' "
            f"branch_name='{git_info.branch_name}' "
            f"remote_url='{git_info.remote_url}'"
        )

        # Load default versions
        default_versions = load_default_versions(pulumi_config)

        # Create the initialization config
        init_config = InitializationConfig(
            pulumi_config=pulumi_config,
            stack_name=stack_name,
            project_name=project_name,
            default_versions=default_versions,
            git_info=git_info,
            metadata={}
            # ... other initializations
        )

        return init_config

    except Exception as e:
        log.error(f"Failed to initialize Pulumi: {str(e)}")
        raise
```

### `config.py`

**Purpose**: Manages advanced configuration retrieval, merging, and validation.

**Key Responsibilities**:

- Retrieve configurations from various sources.
- Merge configurations with proper precedence.
- Validate configurations using Pydantic models.
- Cache and load default versions for modules.

**Overview**:

The `config.py` module provides functions to manage configurations at different layers, ensuring that modules receive the correct settings.

**Example Functions**:

```python
def get_module_config(
    module_name: str,
    config: pulumi.Config,
    default_versions: Dict[str, str],
    namespace: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    """Retrieves and prepares the configuration for a module."""

def load_default_versions(
    config: pulumi.Config,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Loads the default versions for modules based on configuration settings."""

def validate_module_config(
    module_name: str,
    config: Dict[str, Any],
    module_class: Optional[type[ModuleBase]] = None
) -> None:
    """Validates module configuration against its schema."""
```

### `deployment.py`

**Purpose**: Orchestrates the deployment of modules based on the configuration.

**Key Responsibilities**:

- Dynamically import and deploy enabled modules.
- Manage module dependencies and order of deployment.
- Handle deployment errors and logging.

**Overview**:

The `DeploymentManager` class is responsible for coordinating the deployment of modules, ensuring that they are deployed in the correct order and with the necessary configurations.

**Example**:

```python
from typing import List, Dict
import importlib
from pulumi import log

class DeploymentManager:
    """
    Manages the deployment of modules based on the configuration.
    """

    def __init__(self, init_config: InitializationConfig):
        self.init_config = init_config
        self.deployed_modules: Dict[str, ModuleDeploymentResult] = {}

    def deploy_modules(self, modules_to_deploy: List[str]) -> None:
        """Deploys the enabled modules."""
        for module_name in modules_to_deploy:
            try:
                self.deploy_module(module_name)
            except Exception as e:
                log.error(f"Failed to deploy module {module_name}: {str(e)}")

    def deploy_module(self, module_name: str) -> None:
        """Deploys a single module by dynamically importing and executing its deploy function."""
        try:
            # Dynamically import the module's deploy function
            deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
            deploy_func = getattr(deploy_module, "deploy", None)

            if not callable(deploy_func):
                raise AttributeError(f"Module {module_name} does not have a deploy function.")

            # Retrieve the module configuration
            module_config = self.init_config.pulumi_config.get_object(module_name) or {}

            # Call the deploy function with the necessary arguments
            result = deploy_func(
                config=module_config,
                init_config=self.init_config,
            )

            # Store the deployment result
            self.deployed_modules[module_name] = result

        except ImportError as e:
            log.error(f"Module {module_name} could not be imported: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error deploying module {module_name}: {str(e)}")
            raise
```

### `metadata.py`

**Purpose**: Manages global metadata, labels, and annotations to be applied to resources.

**Key Responsibilities**:

- Initialize and store global metadata in a thread-safe manner.
- Provide functions to set global labels and annotations.
- Apply global metadata to resources during creation.

**Overview**:

The `MetadataSingleton` class ensures consistent metadata is applied across all resources, supporting compliance and organizational policies.

**Example**:

```python
from typing import Dict

class MetadataSingleton:
    """Thread-safe singleton class to manage global metadata."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._global_labels: Dict[str, str] = {}
        self._global_annotations: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()
                    cls._instance = instance
        return cls._instance

    @property
    def global_labels(self) -> Dict[str, str]:
        """Get global labels."""
        return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        """Get global annotations."""
        return self._global_annotations.copy()

    def set_labels(self, labels: Dict[str, str]) -> None:
        """Set global labels."""
        self._global_labels = labels.copy()

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        """Set global annotations."""
        self._global_annotations = annotations.copy()
```

### `git.py`

**Purpose**: Provides utility functions for interacting with Git repositories.

**Key Responsibilities**:

- Collect Git repository information such as commit hash, branch name, and remote URL.
- Sanitize Git information for use in resource metadata.
- Extract repository name from remote URLs.

**Overview**:

The `git.py` module allows the inclusion of Git metadata in resource annotations, aiding in traceability and compliance.

**Example**:

```python
def collect_git_info() -> GitInfo:
    """Collects Git repository information."""

def sanitize_git_info(git_info: Dict[str, str]) -> Dict[str, str]:
    """Sanitizes git information for use in resource tags/labels."""

def extract_repo_name(remote_url: str) -> str:
    """Extracts the repository name from a Git remote URL."""
```

### `types.py`

**Purpose**: Defines shared data classes, types, and models used across modules.

**Key Responsibilities**:

- Provide type-safe configurations using Pydantic models and `TypedDict`.
- Define data structures for initialization, compliance, and module configurations.

**Overview**:

Using strict typing ensures robustness and prevents runtime errors due to type mismatches.

**Example**:

```python
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class GitInfo(BaseModel):
    commit_hash: str = 'unknown'
    branch_name: str = 'unknown'
    remote_url: str = 'unknown'

class InitializationConfig(BaseModel):
    """Configuration for core module initialization."""
    pulumi_config: pulumi.Config
    stack_name: str
    project_name: str
    default_versions: Dict[str, Any]
    git_info: GitInfo
    metadata: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {"labels": {}, "annotations": {}}
    )
    # ... other fields

    @property
    def config(self) -> Any:
        """Provides backwards compatibility for config access."""
        return self.pulumi_config

    class Config:
        arbitrary_types_allowed = True

class ComplianceConfig(BaseModel):
    """Compliance configuration settings."""
    fisma: FismaConfig = Field(default_factory=FismaConfig)
    nist: NistConfig = Field(default_factory=NistConfig)
    scip: ScipConfig = Field(default_factory=ScipConfig)
    # ... methods for merging configurations
```

### `interfaces.py`

**Purpose**: Defines shared interfaces and protocols to ensure consistent implementations.

**Key Responsibilities**:

- Define protocols for deployment contexts and module interfaces.
- Provide base classes for resource managers.

**Overview**:

Using protocols from the `typing` module allows for the definition of expected behaviors, aiding in code consistency.

**Example**:

```python
from typing import Protocol, Dict, Any, List

class DeploymentContext(Protocol):
    """Protocol defining the deployment context interface."""
    def get_config(self) -> Dict[str, Any]: ...
    def deploy(self) -> ModuleDeploymentResult: ...

class ModuleInterface(Protocol):
    """Protocol defining required module interface."""
    def validate_config(self, config: Dict[str, Any]) -> List[str]: ...
    def deploy(self, ctx: DeploymentContext) -> ModuleDeploymentResult: ...
    def get_dependencies(self) -> List[str]: ...

class ResourceManagerInterface(Protocol):
    """Protocol for resource managers."""
    def get_or_create(self) -> tuple[Any, Dict[str, Any]]: ...
    def deploy_resources(self) -> Dict[str, Any]: ...
```

---

### `utils.py`

**Purpose**: Contains general utility functions used across the core module.

**Key Responsibilities**:

- Provide common utility functions (e.g., setting resource metadata).
- Enhance performance and code reusability.
- Support other core components with shared functionalities.

**Example**:

```python
def set_resource_metadata(
    metadata: Dict[str, Any],
    labels: Dict[str, str],
    annotations: Dict[str, str]
) -> None:
    """Sets metadata for a resource, merging global labels and annotations."""

def generate_global_transformations() -> List[Callable]:
    """Generates resource transformations to apply global metadata."""
```

---

## Configuration Management

### Layers of Configuration

Configurations are merged and resolved in the following order of precedence:

1. **Global Defaults**: Baseline settings applicable to all modules.
2. **User-Specified Sources**: Configurations specified via Pulumi config or command-line.
3. **Stack-Specific Overrides**: Customizations for specific Pulumi stacks.
4. **Local Default Versions**: Default versions of modules defined in the codebase.
5. **Remote Versions**: Versions fetched from remote sources based on channels.

### Default Module Configuration

The `DEFAULT_MODULE_CONFIG` dictionary defines which modules are enabled by default and their default configurations.

> TODO: relocate default module configuration to the module's configuration files and remove from core module

**Example**:

```python
DEFAULT_MODULE_CONFIG: Dict[str, ModuleDefaults] = {
    "aws": {"enabled": False, "version": None, "config": {}},
    "cert_manager": {"enabled": False, "version": None, "config": {}},
    "kubevirt": {"enabled": False, "version": None, "config": {}},
    # ... other modules
}
```

---

## Initialization Flow

The initialization process involves:

- Loading Pulumi configuration and stack information.
- Collecting Git metadata.
- Loading default module versions and configurations.
- Initializing global metadata settings.

---

## Deployment Orchestration

The `DeploymentManager` handles the deployment process:

- **Module Discovery**: Dynamically discovers modules and determines which ones are enabled for deployment.
- **Initialization**: Loads configurations and initializes modules.
- **Deployment Execution**: Calls each module's deploy function with appropriate contexts.
- **Error Handling**: Logs errors and manages exceptions during deployment.

---

## Metadata and Tagging

Consistent metadata and tagging are crucial for:

- **Compliance**: Meeting organizational and regulatory requirements.
- **Traceability**: Tracking resource changes and deployments.
- **Management**: Facilitating resource identification and categorization.

Ensures that global labels and annotations are applied uniformly across all resources.

---

## Type Definitions and Schemas

Using Pydantic models and type hints:

- **Enhances Type Safety**: Reduces runtime errors due to type mismatches.
- **Improves Readability**: Makes code self-documenting and easier to understand.
- **Facilitates Validation**: Ensures data structures conform to expected formats.

---

## Git Utilities

Include functions to collect and sanitize Git repository information for inclusion in resource metadata, aiding in traceability and compliance.

---

## Interfaces and Protocols

Define standard interfaces that modules and resources should implement to ensure consistency across the platform, promoting a modular and extensible design.

---

## Utility Functions

Include general-purpose functions that support the core module's functionality, such as merging configurations or setting resource metadata.

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

- **Type Annotations**: Use type hints and Pydantic models extensively.
- **Documentation**: Provide comprehensive docstrings and inline comments.
- **Compliance Adherence**: Utilize compliance configurations and metadata.
- **Error Handling**: Implement robust error handling with meaningful messages.
- **Modular Design**: Keep code organized and modular for maintainability.
- **Testing**: Write unit and integration tests to ensure code reliability.

---

## Development Guidelines

- **Follow Coding Standards**: Adhere to PEP 8 and PEP 257 for code style.
- **Type Safety**: Enforce strict type checking using tools like Pyright.
- **Version Control**: Use meaningful commit messages and follow branching strategies.
- **Continuous Integration**: Integrate automated testing and linting in the development workflow.

---

## Contribution Guidelines

- **Discuss Changes**: Engage with maintainers before implementing significant changes.
- **Code Quality**: Write clean, type-safe code with proper documentation.
- **Pull Requests**: Provide detailed descriptions and be open to feedback.

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
