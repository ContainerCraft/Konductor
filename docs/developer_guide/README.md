# Konductor Developer Guide

Welcome to the Konductor Developer Guide! This comprehensive guide is designed for developers who want to contribute to or extend the Konductor Infrastructure as Code (IaC) platform. Whether you're fixing bugs, adding features, or creating new modules, this guide will help you understand our development practices and standards.

## Table of Contents

1. [Introduction](#introduction)
   - [What is Konductor?](#what-is-konductor)
   - [Development Philosophy](#development-philosophy)
   - [How to Use This Guide](#how-to-use-this-guide)

2. [Getting Started](#getting-started)
   - [Development Environment Setup](#development-environment-setup)
   - [Repository Structure](#repository-structure)
   - [Core Technologies](#core-technologies)

3. [Development Standards](#development-standards)
   - [Code Quality Requirements](#code-quality-requirements)
   - [Type Safety with TypedDict](#type-safety-with-typeddict)
   - [Documentation Requirements](#documentation-requirements)
   - [Testing Standards](#testing-standards)

4. [Module Development](#module-development)
   - [Module Architecture](#module-architecture)
   - [Creating New Modules](#creating-new-modules)
   - [Module Testing](#module-testing)
   - [Module Documentation](#module-documentation)

5. [Contributing](#contributing)
   - [Contribution Workflow](#contribution-workflow)
   - [Pull Request Guidelines](#pull-request-guidelines)
   - [Code Review Process](#code-review-process)

6. [Available Modules](#available-modules)
   - [AWS Module](#aws-module)
   - [Cert Manager Module](#cert-manager-module)
   - [Other Modules](#other-modules)

7. [Additional Resources](#additional-resources)
   - [Reference Documentation](#reference-documentation)
   - [Community Resources](#community-resources)
   - [Getting Help](#getting-help)

## Introduction

### What is Konductor?

Konductor is a modern Infrastructure as Code (IaC) platform built on Pulumi and Python, designed to streamline DevOps workflows and Platform Engineering practices. It provides a robust framework for managing cloud infrastructure with emphasis on type safety, modularity, and maintainability.

### Development Philosophy

Our development approach is guided by several key principles:

- **Type Safety**: We use Python's type system and TypedDict to catch errors early.
- **Modularity**: Code is organized into reusable, self-contained modules.
- **Documentation**: Comprehensive documentation is treated as a first-class citizen.
- **Testing**: Thorough testing ensures reliability and maintainability.
- **Accessibility**: Code and documentation should be accessible to developers of all skill levels.

### How to Use This Guide

This guide is organized to support different development activities:

- **New Contributors**: Start with [Getting Started](#getting-started) and [Contributing](#contributing).
- **Module Developers**: Focus on [Module Development](#module-development).
- **Core Contributors**: Review all sections, particularly [Development Standards](#development-standards).

## Getting Started

### Development Environment Setup

1. **Prerequisites**:
   - Python 3.8+
   - Poetry for dependency management
   - Pulumi CLI
   - Git
   - VS Code (recommended)

2. **Initial Setup**:
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

3. **VS Code Configuration**:
   - Install recommended extensions
   - Configure Pylance for type checking
   - Set up the Dev Container (optional but recommended)

### Repository Structure

```bash
konductor/
├── __main__.py
├── modules
│ ├── aws
│ │   ├── config.py
│ │   ├── <other_module_files>
│ │   └── types.py
│ └── core
│     ├── config.py
│     ├── deployment.py
│     ├── __init__.py
│     ├── metadata.py
│     ├── resource_helpers.py
│     ├── types.py
│     └── utils.py
├── docs/ # Documentation
└── tests/ # Test suite
```


### Core Technologies

- **Pulumi**: Infrastructure as Code framework
- **Poetry**: Dependency management
- **TypedDict**: Type-safe configuration management
- **Pyright**: Static type checking

## Development Standards

For detailed standards, refer to our [Python Development Standards](../reference/PULUMI_PYTHON.md).

### Code Quality Requirements

- Static type checking with Pyright
- PEP 8 compliance
- Documentation for all public APIs
- Unit tests for new functionality

### Type Safety with TypedDict

We use TypedDict for configuration management. See our [TypedDict Guide](../reference/TypedDict.md) for details.

### Documentation Requirements

All code contributions must include:

- Docstrings for modules, classes, and functions
- Updated README files
- Changelog entries
- Type annotations

### Testing Standards

- Unit tests for new functionality
- Integration tests for modules
- Type checking passes without errors
- Test coverage requirements met

## Module Development

### Module Architecture

Modules follow a standard structure:

```bash
modules/<module_name>/
├── init.py
├── types.py # TypedDict definitions
├── deploy.py # Deployment logic
└── README.md # Module documentation
```


### Creating New Modules

See our detailed [Module Development Guide](./modules/README.md).

### Module Testing

Refer to our [Testing Guide](./contribution_guidelines.md#testing) for module testing requirements.

### Module Documentation

Each module must include:

- README with usage instructions
- Configuration documentation
- Example configurations
- Troubleshooting guide

## Contributing

### Contribution Workflow

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Run tests and type checking
5. Submit a pull request

### Pull Request Guidelines

See our [Pull Request Template](../contribution_templates/pull_request_template.md).

### Code Review Process

All contributions undergo review for:

- Code quality
- Documentation completeness
- Test coverage
- Type safety

## Available Modules

### AWS Module

- [Developer Guide](./modules/aws/developer_guide.md)
- [Implementation Roadmap](./modules/aws/implementation_roadmap.md)

### Cert Manager Module

- [Developer Guide](./modules/cert_manager/developer_guide.md)

### Other Modules

See our [Modules Directory](./modules/README.md) for a complete list.

## Additional Resources

### Reference Documentation

- [Pulumi Python Standards](../reference/PULUMI_PYTHON.md)
- [TypedDict Guide](../reference/TypedDict.md)
- [Style Guide](../reference/style_guide.md)

### Community Resources

- [Discord Community](https://discord.gg/Jb5jgDCksX)
- [GitHub Discussions](https://github.com/containercraft/konductor/discussions)

### Getting Help

- Join our [Discord](https://discord.gg/Jb5jgDCksX)
- Open an [issue](https://github.com/containercraft/konductor/issues)
- Check our [FAQ](../user_guide/faq_and_troubleshooting.md)

---

**Next Steps**: Review our [Contribution Guidelines](./contribution_guidelines.md) to start contributing to Konductor.
