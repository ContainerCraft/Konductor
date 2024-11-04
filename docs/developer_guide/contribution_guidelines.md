# Contribution Guidelines

## Introduction

Welcome to the Konductor contribution guidelines! This document provides detailed instructions for contributing to the Konductor project, whether you're fixing bugs, adding features, improving documentation, or creating new modules. We value all contributions and want to make the process as transparent and straightforward as possible.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment](#development-environment)
4. [Contribution Workflow](#contribution-workflow)
5. [Documentation Guidelines](#documentation-guidelines)
6. [Testing Requirements](#testing-requirements)
7. [Code Style and Standards](#code-style-and-standards)
8. [Pull Request Process](#pull-request-process)
9. [Issue Guidelines](#issue-guidelines)
10. [Community Engagement](#community-engagement)

## Code of Conduct

Our project adheres to a Code of Conduct that establishes expected behavior for all contributors and community members. Please read and follow our [Code of Conduct](../CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher
- Poetry for dependency management
- Pulumi CLI
- Git
- A code editor (VS Code recommended)
- AWS CLI (for AWS module development)
- kubectl (for Kubernetes development)

### Initial Setup

1. **Fork the Repository**
   ```bash
   # Fork via GitHub UI, then clone your fork
   git clone https://github.com/YOUR_USERNAME/konductor.git
   cd konductor
   ```

2. **Set Up Development Environment**
   ```bash
   # Install dependencies
   poetry install

   # Activate virtual environment
   poetry shell

   # Install pre-commit hooks
   pre-commit install
   ```

## Development Environment

### Required Tools

- **VS Code Extensions**:
  - Pylance for Python language support
  - Python extension for debugging
  - YAML extension for configuration files
  - Docker extension for container management

### Configuration Files

1. **Pyright Configuration** (`pyrightconfig.json`):
   ```json
   {
     "include": ["**/*.py"],
     "exclude": ["**/__pycache__/**"],
     "reportMissingImports": true,
     "pythonVersion": "3.8",
     "typeCheckingMode": "strict"
   }
   ```

2. **Poetry Configuration** (`pyproject.toml`):
   ```toml
   [tool.poetry]
   name = "konductor"
   version = "0.1.0"
   description = "Infrastructure as Code platform"

   [tool.poetry.dependencies]
   python = "^3.8"
   pulumi = "^3.0.0"
   ```

## Contribution Workflow

### 1. Create an Issue

Before starting work:
- Check existing issues and discussions
- Create a new issue using the appropriate template:
  - [Bug Report Template](../contribution_templates/issue_template.md)
  - [Feature Request Template](../contribution_templates/feature_request_template.md)

### 2. Branch Creation

```bash
#Create a feature branch
git checkout -b feature/issue-number-brief-description

# For bug fixes
git checkout -b fix/issue-number-brief-description
```


### 3. Development Process

1. **Write Code**
   - Follow [Python Development Standards](../reference/PULUMI_PYTHON.md)
   - Use type hints and TypedDict (see [TypedDict Guide](../reference/TypedDict.md))
   - Add tests for new functionality

2. **Local Testing**
   ```bash
   # Run type checking
   poetry run pyright

   # Run tests
   poetry run pytest

   # Run linting
   poetry run black .
   poetry run isort .
   poetry run flake8 .
   ```

3. **Commit Changes**
   ```bash
   # Stage changes
   git add .

   # Commit with conventional commit message
   git commit -m "type(scope): description"
   ```

### 4. Documentation Updates

All contributions must include appropriate documentation updates:

1. **Code Documentation**
   - Docstrings for all public functions/classes
   - Type annotations
   - Inline comments for complex logic

2. **User Documentation**
   - Update relevant user guides
   - Add examples if applicable
   - Update FAQs if needed

3. **Developer Documentation**
   - Update technical documentation
   - Add architecture diagrams if needed
   - Update module documentation

## Documentation Guidelines

### File Organization

Follow the documentation structure:

```bash
docs/
├── user_guide/ # End-user documentation
├── developer_guide/ # Developer documentation
├── modules/ # Module-specific guides
├── reference/ # Technical references
└── contribution_templates/ # Contribution templates
```

### Documentation Standards

1. **Markdown Formatting**
   - Use ATX-style headers (`#` for headers)
   - Include table of contents for long documents
   - Use code blocks with language identifiers
   - Include alt text for images

2. **Content Guidelines**
   - Write in clear, concise language
   - Include examples and use cases
   - Link to related documentation
   - Keep technical accuracy

3. **Accessibility**
   - Use proper heading hierarchy
   - Provide alt text for images
   - Ensure sufficient color contrast
   - Use descriptive link text

### Example Documentation

```python
from typing import Dict, Optional

def update_resource_tags(
    resource_id: str,
    tags: Dict[str, str],
    region: Optional[str] = None
) -> Dict[str, str]:
    """Update tags for an AWS resource.

    Args:
        resource_id: The ID of the resource to update
        tags: Dictionary of tags to apply
        region: Optional AWS region (defaults to current)

    Returns:
        Dictionary of applied tags

    Raises:
        ResourceNotFoundError: If resource doesn't exist
        InvalidTagError: If tags are invalid

    Example:
        >>> tags = update_resource_tags("vpc-123", {"Environment": "prod"})
        >>> assert tags["Environment"] == "prod"
    """
```


## Testing Requirements

### Required Tests

1. **Unit Tests**
   - Test individual components
   - Use pytest fixtures
   - Mock external dependencies

2. **Integration Tests**
   - Test module interactions
   - Verify resource creation
   - Test configuration handling

3. **Type Checking**
   - Use strict type checking
   - Verify all type annotations

### Example Test Structure

```python
import pytest
from pulumi import automation as auto

def test_vpc_creation():
    """Test VPC creation with default configuration."""
    stack = auto.create_stack(...)

    # Deploy resources
    result = stack.up()

    # Verify outputs
    assert "vpc_id" in result.outputs
    assert result.outputs["vpc_id"].value != ""
```


## Code Style and Standards

### Python Standards

1. **Type Safety**
   - Use type hints for all functions
   - Implement TypedDict for configurations
   - Enable strict type checking

2. **Code Organization**
   - Follow single responsibility principle
   - Use meaningful names
   - Keep functions focused and small

3. **Error Handling**
   - Use custom exceptions
   - Provide meaningful error messages
   - Handle edge cases

### Example Code Style

```python
from typing import TypedDict, List

class NetworkConfig(TypedDict):
    vpc_cidr: str
    subnet_cidrs: List[str]

class NetworkManager:
    """Manages AWS networking resources."""
    def __init__(self, config: NetworkConfig):
        self.config = config
        self.validate_config()

    def validate_config(self) -> None:
        """Validate network configuration."""
        if not self.is_valid_cidr(self.config["vpc_cidr"]):
            raise ValueError(f"Invalid VPC CIDR: {self.config['vpc_cidr']}")
```


## Pull Request Process

### 1. Prepare Your PR

- Update your branch with main
- Ensure all tests pass
- Update documentation
- Add changelog entry

### 2. Submit PR

Use the [Pull Request Template](../contribution_templates/pull_request_template.md):

- Link related issues
- Describe changes
- List testing performed
- Note documentation updates

### 3. Review Process

- Address reviewer feedback
- Keep PR focused and small
- Maintain clear communication

### 4. Merge Requirements

- Passing CI/CD checks
- Approved reviews
- Updated documentation
- Changelog entry

## Issue Guidelines

### Creating Issues

Use appropriate templates:
- [Bug Report Template](../contribution_templates/issue_template.md)
- [Feature Request Template](../contribution_templates/feature_request_template.md)

### Issue Labels

- `bug`: Bug reports
- `enhancement`: Feature requests
- `documentation`: Documentation updates
- `good first issue`: Beginner-friendly
- `help wanted`: Community input needed

## Community Engagement

### Communication Channels

- GitHub Issues and Discussions
- Discord Community

### Getting Help

1. Check documentation
2. Search existing issues
3. Ask in Discord
4. Create a new issue

## Conclusion

Thank you for contributing to Konductor! Your efforts help make the project better for everyone. Remember to:

- Follow the guidelines
- Write clear documentation
- Test thoroughly
- Engage with the community

For updates and new features, watch our [GitHub repository](https://github.com/containercraft/konductor).
