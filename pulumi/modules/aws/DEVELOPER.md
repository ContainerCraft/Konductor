# Konductor Developer Guide

## Introduction

This document is intended for developers who want to contribute to the Konductor IaC codebase. It provides insights into the code structure, development best practices, and the contribution workflow. By adhering to these guidelines, developers can ensure that their contributions align with the project's standards and quality expectations.

---

## Table of Contents

1. [Code Structure](#code-structure)
2. [Development Best Practices](#development-best-practices)
3. [Contribution Workflow](#contribution-workflow)
4. [Adding Enhancements and Features](#adding-enhancements-and-features)
5. [Testing and Validation](#testing-and-validation)
6. [Documentation Standards](#documentation-standards)
7. [Support and Resources](#support-and-resources)

---

## Code Structure

The project is organized into modular components to ensure scalability and maintainability. Below is an overview of the key components:

- __`__main__.py`__: The entry point of the Pulumi program.
- **`core/`**: Contains shared utilities and libraries.
   - **`config.py`**: Handles configuration loading and validation using Pydantic.
   - **`deployment.py`**: Manages deployment orchestration and module integration.
   - **`metadata.py`**: Manages global metadata, labels, and annotations.
   - **`utils.py`**: Provides generic utility functions.

- **`modules/`**: Contains individual modules, each in its own directory.
   - __`modules/<module_name>/types.py`__: Defines Pydantic models for module configurations.
   - __`modules/<module_name>/deploy.py`__: Contains module-specific deployment logic.
   - __`modules/<module_name>/*.py`__: Contains other module-specific functions and components.
   - __`modules/<module_name>/README.md`__: Module-specific documentation.

- **`requirements.txt`**: Lists the dependencies for the project.

### Example Directory Structure

```
pulumi/
├── __main__.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── deployment.py
│   ├── metadata.py
│   └── utils.py
├── modules/
│   ├── aws/
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── deploy.py
│   │   ├── # Other components...
│   │   └── README.md
│   ├── cert_manager/
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── deploy.py
│   │   ├── # Other components...
│   │   └── README.md
│   └── # Other modules...
├── requirements.txt
└── # Other files...
```

---

## Development Best Practices

### Code Hygiene

- **Modularity**: Break down functions and logic into small, reusable components.
- **Type Annotations**: Use type hints throughout the code for better readability and tooling support.
- **Docstrings and Comments**: Document code extensively using docstrings and inline comments.
- **Error Handling**: Implement robust error handling and logging for easier debugging.
- **Resource Options**: Use `ResourceOptions` to manage resource dependencies and parent-child relationships.

### Naming Conventions

- __Files and Directories__: Use `snake_case` for file and directory names.
- **Classes**: Use `PascalCase` for class names.
- __Variables and Functions__: Use `snake_case` for variable and function names.
- __Constants__: Use `UPPER_SNAKE_CASE` for constants.

### Configuration Management

- **Use Pydantic Models**: Define configurations using Pydantic models in `types.py`.
- **Validation**: Include validation logic within the models to ensure configurations are correct before deployment.
- **Default Values**: Provide sensible default values for configuration fields.

### Module Integration

- **Deployment Functions**: Follow the standard function signature for deployment functions.

```python
def deploy_<module_name>(
    config: ModuleNameConfig,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
) -> pulumi.Resource:
    # Deployment logic
```

- __Configuration Loading__: Use the `get_module_config` function to load and validate configurations.

- **Providers**: Access required providers from the `providers` dictionary passed to deployment functions.

---

## Contribution Workflow

### Fork and Clone the Repository

1. **Fork the repository** on GitHub.

2. **Clone the forked repository** to your local machine.

```sh
git clone https://github.com/your-username/konductor.git
cd konductor/pulumi
```

### Set Up Development Environment

1. **Create a virtual environment**:

```sh
python -m venv venv
source venv/bin/activate
```

2. **Install dependencies**:

```sh
pip install -r requirements.txt
```

3. **Configure Pulumi**:

```sh
pulumi login
pulumi stack init dev
```

4. **Set Up Cloud Provider Credentials**:

- For AWS:

```sh
aws configure
```

- For other providers, follow their respective setup instructions.

### Create a Feature Branch

```sh
git checkout -b feature/new-module
```

### Implement Changes

1. **Develop the module** following the guidelines in this document.
2. **Add or modify code** in the appropriate modules.
3. **Write tests** for your changes (if applicable).
4. **Ensure code quality** by running linters and formatters.

### Commit and Push

1. **Commit your changes** with clear and concise messages.

```sh
git add .
git commit -m "Add new module: description"
```

2. **Push to your fork**:

```sh
git push origin feature/new-module
```

### Create a Pull Request

1. **Go to the original repository** on GitHub.
2. **Open a pull request** from your feature branch.
3. **Provide a detailed description** of the changes made and any relevant context or documentation.

---

## Adding Enhancements and Features

### Example: Adding a New Module

1. **Create Module Directory**:

```sh
mkdir modules/new_module
touch modules/new_module/__init__.py
```

2. **Define Configuration Model**:

```python
# modules/new_module/types.py

from pydantic import BaseModel

class NewModuleConfig(BaseModel):
    enabled: bool = False
    # ... other configuration fields ...
```

3. **Implement Deployment Logic**:

```python
# modules/new_module/deploy.py

def deploy_new_module(
    config: NewModuleConfig,
    global_depends_on: List[pulumi.Resource],
    providers: Dict[str, Any],
) -> pulumi.Resource:
    # Deployment logic
```

4. __Update `__main__.py`__:
   - Add the module to `modules_to_deploy`.
   - Ensure the module is correctly loaded and deployed.

---

## Testing and Validation

- **Unit Tests**: Write unit tests for critical functions and logic.
- **Integration Tests**: Test module integration with the core system.
- **Pulumi Preview**: Use `pulumi preview` to validate infrastructure changes.
- **Code Review**: Request reviews from team members to ensure code quality.

---

## Documentation Standards

- **Module README**: Each module should have a `README.md` explaining its purpose, configuration options, and usage instructions.
- **Docstrings**: Use Google or NumPy style docstrings for functions and classes.
- **Inline Comments**: Add comments to explain complex logic or decisions.
- **Change Logs**: Maintain a `CHANGELOG.md` if applicable.

---

## Support and Resources

- **Slack Channel**: Join the project's Slack channel for real-time communication.
- **Issue Tracker**: Use GitHub Issues to report bugs or request features.
- **Wiki**: Refer to the project wiki for additional resources and guides.
