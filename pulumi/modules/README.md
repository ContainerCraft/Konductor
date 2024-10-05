# Konductor User Guide

Welcome to the **Konductor IaC Platform Engineering User Guide**. This document provides an in-depth overview of the design principles, code structure, and best practices for developing and maintaining modules within the Konductor IaC codebase. It is intended for both DevOps Template users and Konductor Template Developers to understand, contribute, and confidently work with the project's architecture and features.

---

## Table of Contents

- [Introduction](#introduction)
- [Design Principles](#design-principles)
- [Code Structure](#code-structure)
- [Configuration Management with Pydantic](#configuration-management-with-pydantic)
  - [Why Pydantic?](#why-pydantic)
  - [Integration Strategy](#integration-strategy)
- [Module Development Guide](#module-development-guide)
  - [1. Module Configuration](#1-module-configuration)
  - [2. Defining Configuration Models](#2-defining-configuration-models)
  - [3. Module Deployment Logic](#3-module-deployment-logic)
  - [4. Updating `__main__.py`](#4-updating-__main__py)
  - [5. Best Practices](#5-best-practices)
- [Example Module: Cert Manager](#example-module-cert-manager)
  - [Configuration Schema](#configuration-schema)
  - [Configuration Model](#configuration-model)
  - [Deployment Logic](#deployment-logic)
  - [Integration in `__main__.py`](#integration-in-__main__py)
- [Conclusion](#conclusion)

---

## Introduction

Konductor is a Pulumi-based Infrastructure as Code (IaC) platform designed to streamline DevOps workflows and Platform Engineering practices. It leverages Pulumi for IaC and uses Python for scripting and automation. This guide aims to standardize module development by centralizing configuration management using Pydantic, simplifying module code, and promoting consistency across the codebase.

---

## Design Principles

- **Modularity**: Each module should be self-contained, defining its own configuration schema and deployment logic.
- **Centralized Configuration**: Use a centralized mechanism for loading and validating configurations to reduce duplication.
- **Type Safety**: Employ Pydantic models for configuration schemas to ensure type safety and validation.
- **Consistency**: Establish clear patterns and standards for module development to ensure uniformity.
- **Developer Experience (DX)**: Simplify the development process with clear guidelines and reusable components.
- **User Experience (UX)**: Provide clear documentation and error messages to enhance user interaction with the platform.
- **Extensibility**: Allow modules to be easily added or modified without affecting the core system.

---

## Code Structure

- **`__main__.py`**: The entry point of the Pulumi program. Handles global configurations, provider setup, and module deployments.
- **`core/`**: Contains shared utilities and libraries, such as configuration management (`config.py`), deployment orchestration (`deployment.py`), and metadata handling (`metadata.py`).
- **`modules/<module_name>/`**: Each module resides in its own directory under `modules/`, containing its specific configuration models (`types.py`) and deployment logic (`deploy.py`).
- **`modules/<module_name>/types.py`**: Defines Pydantic models for module configurations with default values and validation logic.
- **`modules/<module_name>/deploy.py`**: Contains the module-specific deployment logic, taking in the validated configuration and returning relevant outputs.
- **`modules/<module_name>/*.py`**: Contains additional module-specific scripts or utilities, if needed.
- **`modules/<module_name>/README.md`**: Module-specific documentation with configuration options, features, and usage instructions.
- **`requirements.txt`**: Lists the dependencies for the project, including Pydantic and cloud provider SDKs.

---

## Configuration Management with Pydantic

### Why Pydantic?

- **Type Safety and Validation**: Ensures configurations are type-safe and valid before deployment.
- **Flexibility**: Allows modules to define complex nested configurations and custom validation logic.
- **Error Reporting**: Provides clear and detailed error messages for invalid configurations.
- **Ease of Use**: Simplifies the configuration process for both developers and users.

### Integration Strategy

- **Module Autonomy**: Each module defines its own Pydantic configuration model in `types.py`.
- **Centralized Loading**: A core function handles loading configurations from Pulumi config and passes them to the modules after validation.
- **Consistency**: Modules follow a consistent pattern for defining configurations and deployment functions.

---

## Module Development Guide

### 1. Module Configuration

- **Purpose**: Retrieve and validate the module's configuration using Pydantic models.
- **Implementation**: Use the `get_module_config` function in `core/config.py`.

```python
# core/config.py

from pydantic import ValidationError

def get_module_config(module_name: str, config: pulumi.Config) -> Tuple[Any, bool]:
    module_config_dict = config.get_object(module_name) or {}
    module_enabled = module_config_dict.get('enabled', False)

    # Import the module's configuration class
    types_module = importlib.import_module(f"modules.{module_name}.types")
    ModuleConfigClass = getattr(types_module, f"{module_name.capitalize()}Config")

    try:
        # Create an instance of the configuration model
        config_obj = ModuleConfigClass(**module_config_dict)
    except ValidationError as e:
        # Handle validation errors
        pulumi.log.error(f"Configuration error in module '{module_name}':\n{e}")
        raise

    return config_obj, module_enabled
```

### 2. Defining Configuration Models

- **Purpose**: Define a Pydantic model for the module's configuration with default values and validation logic.
- **Implementation**: Create a `types.py` in the module's directory.

```python
# modules/module_name/types.py

from pydantic import BaseModel, Field, validator

class ModuleNameConfig(BaseModel):
    enabled: bool = False
    version: Optional[str] = "latest"  # For Kubernetes modules
    # ... other configuration fields ...

    @validator('version')
    def check_version(cls, v):
        if v not in ["latest", "stable", "edge"]:
            raise ValueError("Invalid version specified")
        return v
```

### 3. Module Deployment Logic

- **Purpose**: Implement the module's deployment logic using the validated configuration.
- **Implementation**: Create a `deploy.py` in the module's directory.

```python
# modules/module_name/deploy.py

def deploy_module_name(
    config: ModuleNameConfig,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
) -> pulumi.Resource:
    # Module-specific deployment logic
    # Use configuration values directly, e.g., config.version
    # Return the primary resource
```

### 4. Updating `__main__.py`

- **Purpose**: Integrate the module into the main Pulumi program.
- **Implementation**:

```python
# __main__.py

from core.config import get_module_config

# Initialize providers and other global configurations
providers = {
    'aws': aws_provider,
    'k8s': k8s_provider,
    # Add other providers as needed
}

# List of modules to deploy
modules_to_deploy = ["aws", "cert_manager", "kubevirt", "multus"]

# Deploy modules
for module_name in modules_to_deploy:
    config_obj, module_enabled = get_module_config(module_name, config)
    if module_enabled:
        deploy_func = discover_deploy_function(module_name)
        primary_resource = deploy_func(
            config=config_obj,
            global_depends_on=global_depends_on,
            providers=providers,
        )
        global_depends_on.append(primary_resource)
        configurations[module_name] = {"enabled": module_enabled}
    else:
        pulumi.log.info(f"Module {module_name} is not enabled.")
```

### 5. Best Practices

- **Use Pydantic Models**: Define all configurations using Pydantic for validation and type safety.
- **Autonomy**: Modules control their own configuration schema and validation logic.
- **Error Handling**: Provide clear and informative error messages for configuration issues.
- **Documentation**: Document configuration options and usage in module `README.md` files.
- **Consistency**: Follow the established code structure and patterns for module development.
- **Avoid Global Variables**: Pass necessary objects as arguments to functions.

---

## Example Module: Cert Manager

### Configuration Schema

```yaml
# Pulumi configuration (Pulumi.<stack>.yaml)
cert_manager:
  enabled: true
  version: "v1.15.3"
  namespace: "cert-manager"
  install_crds: true
```

### Configuration Model

```python
# modules/cert_manager/types.py

from pydantic import BaseModel

class CertManagerConfig(BaseModel):
    enabled: bool = False
    version: str = "latest"
    namespace: str = "cert-manager"
    install_crds: bool = True
    # ... other fields and validators as needed ...
```

### Deployment Logic

```python
# modules/cert_manager/deploy.py

def deploy_cert_manager(
    config: CertManagerConfig,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
) -> pulumi.Resource:
    k8s_provider = providers.get('k8s')
    # Deployment logic for Cert Manager using config values
    # Return the Helm release resource or primary resource
```

### Integration in `__main__.py`

```python
# __main__.py

config_cert_manager, cert_manager_enabled = get_module_config('cert_manager', config)
if cert_manager_enabled:
    from modules.cert_manager.deploy import deploy_cert_manager
    cert_manager_release = deploy_cert_manager(
        config=config_cert_manager,
        global_depends_on=global_depends_on,
        providers=providers,
    )
    global_depends_on.append(cert_manager_release)
    configurations["cert_manager"] = {"enabled": cert_manager_enabled}
else:
    pulumi.log.info("Cert Manager is not enabled.")
```

---

## Conclusion

By following this guide and utilizing Pydantic for configuration management, developers can create modules that are:

- **Robust**: Type-safe and validated configurations reduce runtime errors.
- **Maintainable**: Clear separation of concerns and consistent patterns simplify maintenance.
- **User-Friendly**: Clear documentation and error messages improve user experience.
- **Extensible**: New modules can be added with minimal changes to the core system.

For any questions or further assistance, please refer to the `DEVELOPER.md` document or reach out to the Konductor development team.

---

## Next Steps

- **Developers**: Start updating or creating modules using the guidelines provided.
- **Users**: Refer to module `README.md` files for configuration options and usage instructions.
- **Contributors**: Follow the contribution guidelines in `DEVELOPER.md` to submit enhancements or bug fixes.
