# Konductor Developer Guide: Building a Scalable and Maintainable Pulumi Python Project

Welcome to the **Konductor Developer Guide**! This comprehensive documentation is designed to help you understand the architecture, design decisions, and best practices for contributing to the Konductor Infrastructure as Code (IaC) platform. Whether you're a junior developer new to IaC or a seasoned engineer, this guide provides the essential knowledge to develop scalable, maintainable, and efficient code in the Konductor project.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [Getting Started](#getting-started)
   - [Development Environment Setup](#development-environment-setup)
   - [Repository Structure](#repository-structure)
   - [Core Technologies](#core-technologies)
4. [Directory Structure](#directory-structure)
5. [Code Organization and Modularization](#code-organization-and-modularization)
6. [Module Development](#module-development)
   - [Module Architecture](#module-architecture)
   - [Creating New Modules](#creating-new-modules)
   - [Module Testing](#module-testing)
   - [Module Documentation](#module-documentation)
7. [Entry Point and Initialization](#entry-point-and-initialization)
8. [Configuration Management](#configuration-management)
9. [Dynamic Module Loading](#dynamic-module-loading)
10. [Type Safety and Static Type Checking](#type-safety-and-static-type-checking)
11. [Dependency Management with Poetry](#dependency-management-with-poetry)
12. [Coding Standards and Best Practices](#coding-standards-and-best-practices)
13. [Testing and Continuous Integration](#testing-and-continuous-integration)
14. [Collaboration and Workflow](#collaboration-and-workflow)
    - [Contribution Workflow](#contribution-workflow)
    - [Pull Request Guidelines](#pull-request-guidelines)
    - [Code Review Process](#code-review-process)
15. [Scaling Considerations](#scaling-considerations)
16. [Additional Considerations](#additional-considerations)
17. [Available Modules](#available-modules)
    - [AWS Module](#aws-module)
    - [Cert Manager Module](#cert-manager-module)
    - [Other Modules](#other-modules)
18. [Conclusion](#conclusion)
19. [Additional Resources](#additional-resources)

---

## Introduction

The Konductor project is a pre-written boilerplate designed to streamline platform engineering and facilitate consistent Infrastructure as Code (IaC) practices across application teams. By leveraging Pulumi with Python, the project allows teams to define infrastructure in a familiar programming language while adhering to best practices in IaC.

Our development approach is guided by several key principles:

- **Type Safety**: Utilize Python's type system, Pydantic models, and `TypedDict` to catch errors early.
- **Modularity**: Organize code into reusable, self-contained modules.
- **Documentation**: Maintain comprehensive documentation as a first-class citizen.
- **Testing**: Ensure reliability and maintainability through thorough testing.
- **Accessibility**: Make code and documentation accessible to developers of all skill levels.
- **Configuration-Driven Deployment**: Enable or disable modules based on configuration for flexible deployments.
- **Lazy Loading of Modules**: Load only necessary modules to optimize performance and resource usage.

This guide provides a detailed roadmap to help you:

- Understand the architectural decisions and design patterns used in Konductor.
- Learn how to organize code effectively for scalability and maintainability.
- Implement dynamic module loading based on configuration.
- Ensure type safety and code reliability using Pydantic, `TypedDict`, and Pyright.
- Collaborate efficiently with other developers in a large codebase.

---

## Project Overview

Konductor aims to:

- **Provide a Shared IaC Style**: Facilitate consistent infrastructure definitions across teams.
- **Enable Dynamic, Configuration-Driven Deployments**: Allow modules to be enabled or disabled based on configuration.
- **Promote Modularity and Reusability**: Encourage code reuse and separation of concerns.
- **Simplify the Entry Point**: Keep the `__main__.py` minimal, delegating complex logic to core modules.
- **Support Lazy Loading of Modules**: Load only necessary modules to optimize performance and resource usage.

---

## Getting Started

### Development Environment Setup

#### Prerequisites

- **Python 3.8+**
- **Poetry** for dependency management
- **Pulumi CLI**
- **Git**
- **Visual Studio Code (recommended)**

#### Initial Setup

```bash
# Clone the repository
git clone https://github.com/containercraft/konductor.git
cd konductor

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Initialize Pulumi
pulumi login
```

#### VS Code Configuration

- **Install Recommended Extensions**:
  - Python extension
  - Pylance (for type checking)
  - Pulumi extension
- **Configure Pylance**:
  - Set `"python.analysis.typeCheckingMode": "strict"` in your `settings.json`.
- **Set Up Dev Container** (optional but recommended):
  - Use the provided `.devcontainer` configuration for a consistent development environment.

### Repository Structure

The repository follows a structured layout to promote clarity and ease of navigation.

```plaintext
konductor/
├── pyproject.toml
├── poetry.lock
├── Pulumi.yaml
├── Pulumi.<stack-name>.yaml
├── README.md
├── LICENSE
├── .gitignore
├── __main__.py
├── core/
│   ├── __init__.py
│   ├── initialization.py
│   ├── config.py
│   ├── metadata.py
│   ├── deployment.py
│   ├── types.py
│   └── utils.py
├── modules/
│   ├── __init__.py
│   ├── aws/
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   ├── types.py
│   │   └── ...
│   ├── azure/
│   │   ├── __init__.py
│   │   ├── deploy.py
│   │   ├── types.py
│   │   └── ...
│   ├── kubernetes/
│       ├── __init__.py
│       ├── deploy.py
│       ├── types.py
│       └── ...
├── config/
│   ├── __init__.py
│   └── base.py
├── common/
│   ├── __init__.py
│   ├── utils.py
│   ├── exceptions.py
│   └── types.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   ├── core/
│   ├── modules/
│   └── ...
├── docs/
│   └── ...
```

---

## Directory Structure

A well-organized directory structure is crucial for collaboration and scalability. The Konductor project follows a modular layout that promotes separation of concerns.

**Explanation:**

- **`konductor/`**: The top-level directory containing all source code.
- **`__main__.py`**: The simplified entry point of the Pulumi project.
- **`core/`**: Contains core functionalities such as initialization, configuration management, metadata setup, and deployment management.
- **`modules/`**: Contains individual modules for different providers (e.g., AWS, Azure, Kubernetes), each with its own deployment logic and types.
- **`config/`**: Contains base configuration classes using Pydantic models.
- **`common/`**: Holds shared utilities, custom exceptions, and common type definitions.
- **`tests/`**: Organized in parallel with the `konductor/` structure for targeted testing.
- **`docs/`**: Contains project documentation.

---

## Code Organization and Modularization

### Module Structure

- **Core Modules (`core/`)**: Centralize initialization, configuration, metadata, and deployment management.
- **Modules (`modules/`)**: Each module represents a deployable unit (e.g., `aws`, `azure`, `kubernetes`) and contains its own deployment logic and types.
- **Configurations (`config/`)**: Use Pydantic models for configuration management.
- **Common Utilities (`common/`)**: Include shared utilities, exceptions, and type definitions.

#### Why Modularize?

- **Separation of Concerns**: Different functionalities are isolated to enhance maintainability.
- **Lazy Loading**: Modules are loaded dynamically based on configuration, optimizing performance.
- **Team Collaboration**: Different teams can work independently on separate modules.

### File Layout Within Modules

Each module in `modules/` should contain:

- **`__init__.py`**: Initializes the module.
- **`deploy.py`**: Contains the `deploy` function that handles the deployment logic for the module.
- **`types.py`**: Defines data classes or Pydantic models for the module's configuration.
- **Additional Files**: Any other module-specific implementation files.

---

## Module Development

### Module Architecture

Modules follow a standard structure:

```plaintext
modules/<module_name>/
├── __init__.py
├── deploy.py        # Deployment logic
├── types.py         # Data classes or Pydantic models for configurations
├── README.md        # Module documentation
└── ...              # Additional module-specific files
```

### Creating New Modules

To create a new module:

1. **Create Module Directory**:

   ```bash
   mkdir modules/<module_name>
   touch modules/<module_name>/__init__.py
   ```

2. **Implement `deploy.py`**:

   - Define a `deploy` function that accepts `config` and `init_config` as parameters.

   ```python
   # modules/<module_name>/deploy.py
   from typing import Any, Dict
   from core.types import InitializationConfig, ModuleDeploymentResult

   def deploy(config: Dict[str, Any], init_config: InitializationConfig) -> ModuleDeploymentResult:
       # Deployment logic here
       pass
   ```

3. **Define Module Configuration Types**:

   - Use Pydantic models or `TypedDict` in `types.py` for configuration.

   ```python
   # modules/<module_name>/types.py
   from typing import TypedDict

   class ModuleConfig(TypedDict):
       enabled: bool
       version: str
       # Additional configuration fields
   ```

4. **Write Module Documentation**:

   - Include a `README.md` with usage instructions, configuration details, and examples.

### Module Testing

- **Unit Tests**: Write unit tests for your module's functionality in `tests/modules/<module_name>/`.
- **Integration Tests**: Include integration tests to verify module interactions if applicable.

### Module Documentation

Each module must include:

- **README.md**: Usage instructions, configuration options, and examples.
- **Configuration Documentation**: Detailed explanation of configuration parameters.
- **Example Configurations**: Provide sample configurations for users.
- **Troubleshooting Guide**: Common issues and solutions.

---

## Entry Point and Initialization

### Simplified Entry Point (`__main__.py`)

The `__main__.py` serves as the minimal entry point, delegating complex logic to core modules.

#### Structure:

```python
# konductor/__main__.py
import sys
import pulumi
from pulumi import log

from core.initialization import initialize_pulumi
from core.config import get_enabled_modules
from core.metadata import setup_global_metadata
from core.deployment import DeploymentManager

def main() -> None:
    try:
        # Initialize Pulumi and load configuration
        init_config = initialize_pulumi()

        # Set up global metadata
        setup_global_metadata(init_config)

        # Get the list of enabled modules from the configuration
        modules_to_deploy = get_enabled_modules(init_config.config)
        log.info(f"Deploying modules: {', '.join(modules_to_deploy)}")

        # Create a DeploymentManager with the initialized configuration
        deployment_manager = DeploymentManager(init_config)

        # Deploy the enabled modules
        deployment_manager.deploy_modules(modules_to_deploy)

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### Best Practices:

- **Keep Entry Point Minimal**: Only include essential orchestration steps.
- **Delegate Logic**: Move complex operations to core modules.
- **Dynamic Module Loading**: Ensure only necessary modules are loaded based on configuration.

### Module Initialization (`__init__.py`)

- **Avoid Heavy Logic**: Keep initialization lightweight.
- **Expose Public API**: Define accessible elements when the module is imported.

---

## Configuration Management

### Using Pydantic for Configuration

Pydantic models provide type safety and validation for configuration data.

#### Example:

```python
# config/base.py
from pydantic import BaseSettings
from typing import List

class BaseConfig(BaseSettings):
    environment: str = 'development'
    debug: bool = False
    modules: List[str] = []

    class Config:
        env_file = '.env'
```

#### Usage:

```python
# core/initialization.py
import pulumi
from config.base import BaseConfig
from core.types import InitializationConfig

def initialize_pulumi() -> InitializationConfig:
    # Load Pulumi configuration
    pulumi_config = pulumi.Config()

    # Create BaseConfig instance
    base_config = BaseConfig()

    # Return an InitializationConfig instance
    return InitializationConfig(config=pulumi_config, base_config=base_config)
```

#### Best Practices:

- **Environment Variables**: Use environment variables for sensitive information.
- **Validation**: Leverage Pydantic's validation to ensure configuration correctness.
- **Default Values**: Provide sensible defaults for configuration parameters.

---

## Dynamic Module Loading

### Configuration-Driven Deployment

Modules are enabled or disabled based on configuration, and only enabled modules are loaded and deployed.

#### Example:

```python
# core/config.py
from typing import List

def get_enabled_modules(config: dict) -> List[str]:
    default_modules = {
        "aws": False,
        "azure": False,
        "kubernetes": False,
    }

    # Load user configuration for modules
    modules_config = config.get("modules") or {}

    # Merge configurations
    merged_modules = {**default_modules, **modules_config}

    # Return enabled modules
    return [module for module, enabled in merged_modules.items() if enabled]
```

### Deployment Manager

Handles dynamic loading and deployment of modules.

#### Example:

```python
# core/deployment.py
import importlib
from pulumi import log
from typing import Any, Dict, List

from core.types import InitializationConfig, ModuleDeploymentResult

class DeploymentManager:
    def __init__(self, init_config: InitializationConfig):
        self.init_config = init_config
        self.deployed_modules: Dict[str, ModuleDeploymentResult] = {}

    def deploy_modules(self, modules_to_deploy: List[str]) -> None:
        for module_name in modules_to_deploy:
            try:
                self.deploy_module(module_name)
            except Exception as e:
                log.error(f"Failed to deploy module {module_name}: {str(e)}")

    def deploy_module(self, module_name: str) -> None:
        try:
            # Dynamically import the module's deploy function
            deploy_module = importlib.import_module(f"modules.{module_name}.deploy")
            deploy_func = getattr(deploy_module, "deploy", None)

            if not callable(deploy_func):
                raise AttributeError(f"Module {module_name} does not have a deploy function.")

            # Retrieve the module configuration
            module_config = self.init_config.config.get_object(module_name) or {}

            # Call the deploy function
            result = deploy_func(config=module_config, init_config=self.init_config)

            # Store the deployment result
            self.deployed_modules[module_name] = result

        except ImportError as e:
            log.error(f"Module {module_name} could not be imported: {str(e)}")
            raise
        except Exception as e:
            log.error(f"Error deploying module {module_name}: {str(e)}")
            raise
```

---

## Type Safety and Static Type Checking

### Using TypedDict for Configurations

`TypedDict` helps define type-safe dictionaries for configurations.

#### Example:

```python
# common/types.py
from typing import TypedDict

class ModuleConfig(TypedDict):
    enabled: bool
    version: str
    config: dict
```

### Enforcing Type Checking with Pyright

Pyright is used for static type checking to ensure code reliability.

#### Installation:

```bash
poetry add --dev pyright
```

#### Configuration:

Create a `pyrightconfig.json` in the project root:

```json
{
  "include": ["konductor/**/*.py"],
  "exclude": ["**/__pycache__/**"],
  "reportMissingImports": true,
  "pythonVersion": "3.8",
  "typeCheckingMode": "strict"
}
```

#### Best Practices:

- **Mandatory Type Hints**: All functions and methods must have type hints.
- **Consistent Usage**: Apply `TypedDict` and Pydantic models across the project.
- **Editor Integration**: Configure your editor (e.g., VS Code) for real-time type checking.

---

## Dependency Management with Poetry

Poetry manages dependencies and virtual environments.

### Initializing the Project

```bash
poetry install
```

### Adding Dependencies

```bash
poetry add pydantic
poetry add --dev pytest
```

### Configuring Pulumi to Use Poetry

Ensure `Pulumi.yaml` specifies Poetry:

```yaml
name: konductor
runtime:
  name: python
  options:
    virtualenv: null
```

### Scripts and Entry Points

Define scripts in `pyproject.toml`:

```toml
[tool.poetry.scripts]
konductor = 'konductor.__main__:main'
```

---

## Coding Standards and Best Practices

### Code Style

- **PEP 8 Compliance**: Follow standard Python style guidelines.
- **Type Hinting**: Use type annotations consistently.
- **Docstrings**: Document modules, classes, and functions using docstrings.

### Consistent Naming Conventions

- **Modules and Files**: Use `snake_case`.
- **Classes**: Use `PascalCase`.
- **Variables and Functions**: Use `snake_case`.

### Error Handling and Exceptions

- **Custom Exceptions**: Define in `common/exceptions.py`.
- **Consistent Error Handling**: Use `try-except` blocks appropriately.
- **Logging**: Use Python's `logging` module with appropriate log levels.

---

## Testing and Continuous Integration

### Testing

- **Structure**: Mirror the application structure within `tests/`.
- **Frameworks**: Use `pytest` for testing.
- **Coverage**: Aim for meaningful tests with high coverage.

### Continuous Integration

- **Automated Testing**: Integrate tests into CI/CD pipelines.
- **Code Quality Checks**: Use `flake8`, `black`, and Pyright for linting and formatting.
- **Static Type Checking**: Enforce with Pyright.

---

## Collaboration and Workflow

### Contribution Workflow

1. **Fork the Repository**: Create a personal fork of the Konductor repository.
2. **Create a Feature Branch**: Use a descriptive name for your branch.

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**: Develop your feature or fix.
4. **Run Tests and Type Checking**:

   ```bash
   pytest
   pyright
   ```

5. **Commit Changes**: Write clear and descriptive commit messages.
6. **Push to Your Fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

7. **Submit a Pull Request**: Open a PR against the `main` branch of the Konductor repository.

### Pull Request Guidelines

- **Follow the PR Template**: Include necessary details as per the [Pull Request Template](../contribution_templates/pull_request_template.md).
- **Link Issues**: Reference any related issues.
- **Include Tests**: Ensure your changes are covered by tests.
- **Pass All Checks**: Your PR should pass CI checks before review.

### Code Review Process

All contributions undergo review for:

- **Code Quality**: Adherence to coding standards and best practices.
- **Documentation**: Completeness and clarity of documentation.
- **Test Coverage**: Adequate tests for new functionality.
- **Type Safety**: Compliance with type checking.

---

## Scaling Considerations

### Performance Optimization

- **Lazy Loading**: Load modules dynamically to optimize resource usage.
- **Caching**: Implement caching strategies if applicable.

### Scalability

- **Horizontal Scaling**: Design for concurrent deployments if necessary.
- **Load Balancing**: Implement strategies to distribute workloads in the application layer.

---

## Additional Considerations

### Security

- **Secure Coding Practices**: Follow best practices to prevent vulnerabilities.
- **Dependency Management**: Regularly update dependencies to patch security issues.

### Documentation Standards

- **Structure**: Organize documentation logically.
- **Accessibility**: Ensure documentation is accessible and user-friendly.

### Logging and Monitoring

- **Centralized Logging**: Implement for easier monitoring and debugging.
- **Monitoring Tools**: Use tools to track application performance and health.

---

## Available Modules

### AWS Module

- **Developer Guide**: [modules/aws/README.md](./modules/aws/README.md)
- **Implementation Roadmap**: [modules/aws/ROADMAP.md](./modules/aws/ROADMAP.md)

### Cert Manager Module

- **Developer Guide**: [modules/cert_manager/README.md](./modules/cert_manager/README.md)

### Other Modules

See our [Modules Directory](./modules/README.md) for a complete list.

---

## Additional Resources

### Reference Documentation

- **Pulumi Python Standards**: [../reference/PULUMI_PYTHON.md](../reference/PULUMI_PYTHON.md)
- **TypedDict Guide**: [../reference/TypedDict.md](../reference/TypedDict.md)
- **Style Guide**: [../reference/style_guide.md](../reference/style_guide.md)

### Community Resources

- **Discord Community**: [https://discord.gg/Jb5jgDCksX](https://discord.gg/Jb5jgDCksX)
- **GitHub Discussions**: [https://github.com/containercraft/konductor/discussions](https://github.com/containercraft/konductor/discussions)

### Getting Help

- **Join our Discord**: [https://discord.gg/Jb5jgDCksX](https://discord.gg/Jb5jgDCksX)
- **Open an Issue**: [https://github.com/containercraft/konductor/issues](https://github.com/containercraft/konductor/issues)
- **Check our FAQ**: [../user_guide/faq_and_troubleshooting.md](../user_guide/faq_and_troubleshooting.md)

### External Resources

- **Pulumi Python Documentation**: [https://www.pulumi.com/docs/intro/languages/python/](https://www.pulumi.com/docs/intro/languages/python/)
- **Pyright Documentation**: [https://github.com/microsoft/pyright](https://github.com/microsoft/pyright)
- **Poetry Documentation**: [https://python-poetry.org/docs/](https://python-poetry.org/docs/)
- **PEP 8 Style Guide**: [https://www.python.org/dev/peps/pep-0008/](https://www.python.org/dev/peps/pep-0008/)
- **Python Logging Documentation**: [https://docs.python.org/3/library/logging.html](https://docs.python.org/3/library/logging.html)
- **TypedDict Documentation**: [https://www.python.org/dev/peps/pep-0589/](https://www.python.org/dev/peps/pep-0589/)
- **Pydantic Documentation**: [https://pydantic-docs.helpmanual.io/](https://pydantic-docs.helpmanual.io/)
