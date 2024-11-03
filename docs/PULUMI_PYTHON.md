# Developer Documentation for Pulumi Projects

This document outlines the development practices, techniques, and requirements for working on our advanced platform engineering Pulumi project. It focuses on ensuring code quality, maintainability, and adherence to modern Python and Pulumi best practices.

## Table of Contents

- [Project Setup](#project-setup)
   - [Dependency Management with Poetry](#dependency-management-with-poetry)
   - [Initializing the Project](#initializing-the-project)

- [Enforcing Type Checking with Pyright](#enforcing-type-checking-with-pyright)
   - [Installing Pyright](#installing-pyright)
   - [Configuring Pyright](#configuring-pyright)
   - [Integrating Pyright with Pulumi](#integrating-pyright-with-pulumi)
   - [Editor Integration](#editor-integration)

- [Using Pythonic Input Types with TypedDict](#using-pythonic-input-types-with-typeddict)
   - [Advantages of TypedDict](#advantages-of-typeddict)
   - [Implementing TypedDict in Resources](#implementing-typeddict-in-resources)
   - [Example: Kubernetes Deployment](#example-kubernetes-deployment)

- [Best Practices](#best-practices)
   - [Adherence to DRY Principle](#adherence-to-dry-principle)
   - [Modular Code Organization](#modular-code-organization)
   - [Consistent Coding Standards](#consistent-coding-standards)

- [Code Standards and Guidelines](#code-standards-and-guidelines)
   - [Naming Conventions](#naming-conventions)
   - [Type Annotations](#type-annotations)
   - [Error Handling](#error-handling)

- [Further Reading](#further-reading)

## Project Setup

### Dependency Management with Poetry

Ensure that `poetry` is added to your system's PATH. Refer to the [official installation guide](https://python-poetry.org/docs/#installation) for detailed instructions.

### Initializing the Project

1. **Initialize Poetry:**

If not already initialized, set up Poetry in the project directory:

```bash
poetry install
```

This command will create a virtual environment and install all dependencies specified in `pyproject.toml`.

We use [Poetry](https://python-poetry.org/) for dependency management and packaging. Poetry ensures that our development environment is consistent, dependencies are properly managed, and collaboration is streamlined.

2. **Activate the Virtual Environment:**

```bash
poetry shell
```

Alternatively, you can prefix commands with `poetry run`.

3. **Configure Pulumi to Use Poetry:**

Ensure that `Pulumi.yaml` specifies Poetry as the toolchain:

```yaml
name: your-pulumi-project
runtime:
  name: python
  options:
    toolchain: poetry
```

4. **Install Pulumi Dependencies:**

```bash
pulumi install
```

This command ensures that Pulumi recognizes and utilizes the Poetry-managed environment.

## Enforcing Type Checking with Pyright

Type checking enhances code reliability and maintainability. We enforce strict type checking using [Pyright](https://github.com/microsoft/pyright).

### Installing Pyright

Add Pyright to the development dependencies:

```bash
poetry add --dev pyright
```

### Configuring Pyright

Create a `pyrightconfig.json` in the project root to define Pyright settings:

```json
{
  "include": ["**/*.py"],
  "exclude": ["**/__pycache__/**"],
  "reportMissingImports": true,
  "pythonVersion": "3.8",
  "typeCheckingMode": "strict"
}
```

- **`include`**: Files to include in type checking.
- **`exclude`**: Files or directories to exclude.
- **`reportMissingImports`**: Reports errors for unresolved imports.
- **`pythonVersion`**: Target Python version.
- **`typeCheckingMode`**: Set to `"strict"` for comprehensive checking.

### Integrating Pyright with Pulumi

Configure Pulumi to run Pyright before deployments:

1. **Update `Pulumi.yaml`:**

```yaml
name: your-pulumi-project
runtime:
  name: python
  options:
    typechecker: pyright
```

2. **Run Pulumi Commands:**

Pyright will automatically run during Pulumi operations:

```bash
pulumi up
```

If type errors are detected, the deployment will halt, and errors will be displayed.

### Editor Integration

For real-time type checking and enhanced development experience:

#### Visual Studio Code with Pylance

1. **Install Pylance Extension:**

   Install the [Pylance extension](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance).

2. **Configure Type Checking Mode:**

Add the following to `settings.json`:

```json
{
  "python.analysis.typeCheckingMode": "strict"
}
```

## Using Pythonic Input Types with TypedDict

We leverage `TypedDict` to define resource inputs using dictionaries with type hints. This approach combines flexibility with type safety.

### Advantages of TypedDict

- **Conciseness**: Reduces boilerplate code.
- **Readability**: Enhances code clarity.
- **Type Safety**: Enables static type checking.
- **Flexibility**: Allows easy manipulation of configurations.

### Implementing TypedDict in Resources

Define custom `TypedDict` classes to specify the expected structure of resource configurations.

#### Example

```python
from typing import TypedDict

class VpcArgs(TypedDict):
    cidr_block: str
    tags: dict

vpc_args: VpcArgs = {
    "cidr_block": "10.0.0.0/16",
    "tags": {
        "Name": "my-vpc",
    },
}
```

### Example: Kubernetes Deployment

Implementing a Kubernetes Deployment using `TypedDict`:

```python
from typing import TypedDict, List
from pulumi_kubernetes.apps.v1 import Deployment

class ContainerPort(TypedDict):
    containerPort: int

class Container(TypedDict):
    name: str
    image: str
    ports: List[ContainerPort]

class PodSpec(TypedDict):
    containers: List[Container]

class PodTemplateSpec(TypedDict):
    metadata: dict
    spec: PodSpec

class DeploymentSpec(TypedDict):
    replicas: int
    selector: dict
    template: PodTemplateSpec

app_labels = {"app": "nginx"}

deployment_spec: DeploymentSpec = {
    "replicas": 3,
    "selector": {"matchLabels": app_labels},
    "template": {
        "metadata": {"labels": app_labels},
        "spec": {
            "containers": [
                {
                    "name": "nginx",
                    "image": "nginx:1.14.2",
                    "ports": [{"containerPort": 80}],
                },
            ],
        },
    },
}

deployment = Deployment(
    "nginx-deployment",
    metadata={
        "name": "nginx-deployment",
        "labels": app_labels
    },
    spec=deployment_spec,
)
```

## Best Practices

- Use consistent key naming (e.g., `matchLabels` instead of `match_labels`) to align with Kubernetes API specifications.
- Define all necessary `TypedDict` classes to cover the nested structure of configurations.
- Leverage type annotations for variables to enhance type checking.

### Adherence to DRY Principle

- **Avoid Repetition**: Use variables and functions to eliminate redundant code.
- **Shared Configurations**: Centralize common configurations or parameters.

### Modular Code Organization

- **Packages and Modules**: Organize code into logical packages and modules.
- **Reusability**: Encapsulate functionality into reusable components.
- **Separation of Concerns**: Divide code based on functionality (e.g., networking, compute resources).

### Consistent Coding Standards

- **PEP 8 Compliance**: Follow Python's style guidelines.
- **Naming Conventions**: Use descriptive and consistent names for variables, functions, and resources.
- **Comments and Documentation**: Provide clear comments and docstrings where necessary.

## Code Standards and Guidelines

### Naming Conventions

- __Variables and Functions__: Use `snake_case`.
- **Classes and Exceptions**: Use `PascalCase`.
- __Constants__: Use `UPPER_SNAKE_CASE`.

### Type Annotations

- **Mandatory Type Hints**: All functions and methods should include type hints for parameters and return types.
- **Variable Annotations**: Use type annotations for variables, especially when the type is not immediately clear.

### Error Handling

- **Explicit Exceptions**: Raise specific exceptions with clear messages.
- **Resource Management**: Ensure resources are properly cleaned up or rolled back on failures.
- **Logging**: Utilize logging for error reporting and debugging.

## References

- **Pulumi Python Documentation**: [Pulumi Python Docs](https://www.pulumi.com/docs/intro/languages/python/)
- **Poetry Documentation**: [Poetry Docs](https://python-poetry.org/docs/)
- **Pyright Documentation**: [Pyright GitHub](https://github.com/microsoft/pyright)
- **PEP 8 Style Guide**: [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **TypedDict Documentation**: [PEP 589 - TypedDict](https://www.python.org/dev/peps/pep-0589/)
