# Module Refactoring Guide

## Overview
This document outlines the standardized approach for refactoring Pulumi infrastructure modules to follow Python best practices while maintaining infrastructure-as-code principles. The goal is to create a consistent, maintainable, and testable module structure across the codebase.

## Core Principles

### 1. Clear Module Interface
- Each module must expose its public API through `__init__.py`
- Use `__all__` to explicitly declare public interfaces
- Provide type hints for all public interfaces
- Document the module's purpose and usage in the module docstring

### 2. Separation of Concerns
Modules should separate functionality into distinct files:
- `__init__.py`: Public API and entry points
- `types.py`: Type definitions and configuration classes
- Resource-specific implementation files (e.g., `provider.py`, `resources.py`)
- No direct resource creation in `__init__.py`

### 3. Object-Oriented Design
- Use classes to encapsulate related functionality
- Prefer composition over inheritance
- Implement clear class responsibilities
- Use properties for computed or lazy-loaded values

### 4. Type Safety
- Use type hints consistently throughout the codebase
- Leverage Pydantic models for configuration validation
- Define clear interfaces using Protocol classes where appropriate
- Use TypedDict for structured dictionary types

## Standard Module Structure

```bash
module/<module_name>/
├── __init__.py
├── types.py
├── provider.py
├── resources.py
├── [component_name].py
└── README.md
```

### File Responsibilities

#### __init__.py
- Expose the public API
- Define the module's entry points
- Import all public interfaces and submodules
- Use `__all__` to manage the public API

```python
"""
Module docstring describing the purpose and functionality of the module.
"""
from typing import List, Optional, Tuple
from .types import ModuleConfig
from .resources import ResourceManager

__all__ = [
    "ModuleConfig",
    "ResourceManager",
    "create_infrastructure"
]

def create_infrastructure(
    config: ModuleConfig,
    dependencies: Optional[List[pulumi.Resource]] = None
) -> Tuple[str, pulumi.Resource, Dict[str, Any]]:
    """
    Create infrastructure with the given configuration.
    """
    pass
```

#### types.py

```python
from typing import TypedDict, Optional
from pydantic import BaseModel

class ModuleConfig(BaseModel):
    """
    Module configuration.
    """
    pass
```

#### resources.py

```python
from pulumi import ProviderResource

class ResourceManager:
    """
    Manages the creation and configuration of module resources.
    """
    def __init__(self, provider: ProviderResource):
        self.provider = provider

    def create_resource(self, config: ModuleConfig) -> pulumi.Resource:
        """
        Create a resource with the given configuration.
        """
        pass
```

## Implementation Requirements

### 1. Configuration Management
- Use Pydantic models for configuration validation
- Support merging of user configs with defaults
- Validate configuration at initialization time
- Support environment variable overrides where appropriate

### 2. Resource Management
- Implement idempotent resource creation
- Handle resource dependencies explicitly
- Support resource tagging and metadata
- Implement proper cleanup and error handling

### 3. Provider Integration
- Abstract provider-specific details
- Support multiple provider configurations
- Handle provider authentication securely
- Support cross-provider dependencies

### 4. Testing Support
- Design classes for testability
- Support mocking of external dependencies
- Enable unit testing of configuration
- Support integration testing of resource creation

## Migration Process

1. **Analysis Phase**
   - Review existing module functionality
   - Identify public interfaces
   - Map resource dependencies
   - Document current configuration options

2. **Refactoring Phase**
   - Create new file structure
   - Implement type definitions
   - Create resource management classes
   - Migrate existing functionality

3. **Testing Phase**
   - Write unit tests
   - Verify existing functionality
   - Test error conditions
   - Validate configuration handling

4. **Documentation Phase**
   - Update module documentation
   - Add docstrings
   - Create usage examples
   - Document breaking changes

## Best Practices

### Code Organization
- Group related functionality into classes
- Use private methods for implementation details
- Implement clear error handling
- Follow PEP 8 style guidelines

### Documentation
- Include docstrings for all public interfaces
- Document configuration options
- Provide usage examples
- Document any breaking changes

### Error Handling
- Use custom exception classes
- Provide meaningful error messages
- Handle resource creation failures
- Implement proper cleanup

### Testing
- Write unit tests for configuration
- Test resource creation logic
- Implement integration tests
- Test error conditions

## Breaking Changes
When refactoring modules, maintain backward compatibility:
- Keep existing entry points functional
- Support old configuration formats
- Document migration paths
- Version breaking changes appropriately

## Example Implementation
See the AWS module implementation as a reference:
- `modules/aws/__init__.py`
- `modules/aws/types.py`
- `modules/aws/resources.py`
- `modules/aws/provider.py`

## Validation Checklist

- [ ] Clear public API in `__init__.py`
- [ ] Type definitions in `types.py`
- [ ] Resource management classes implemented
- [ ] Configuration validation
- [ ] Error handling
- [ ] Documentation
- [ ] Unit tests
- [ ] Integration tests
- [ ] Breaking changes documented
- [ ] Migration guide provided

## Next Steps

1. Complete AWS module refactoring
2. Review and validate changes
3. Create test suite
4. Document changes
5. Apply pattern to remaining modules
6. Validate full codebase
7. Update global documentation

## References

- [Python Package Structure](https://docs.python.org/3/tutorial/modules.html)
- [Type Hints PEP 484](https://www.python.org/dev/peps/pep-0484/)
- [Pulumi Architecture](https://www.pulumi.com/docs/intro/concepts/how-pulumi-works/)
- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
