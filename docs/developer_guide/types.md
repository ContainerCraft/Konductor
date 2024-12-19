# Type Hierarchy Guide

## Overview

This guide defines the standardized type hierarchy pattern for the Konductor Infrastructure as Code (IaC) template project. The type system is designed to support multi-cloud, multi-component infrastructure deployments while maintaining a clean separation of concerns, preventing circular dependencies, and providing an intuitive developer experience.

This document outlines core principles, directory structures, and guidelines for defining and extending types within Konductor’s IaC framework. It ensures that types are strongly typed, well-documented, modular, and leverage Pydantic models for validation and sensible defaults.

## Core Principles

- **Separation of Concerns**: Each module owns its type definitions, ensuring local scope and preventing cross-contamination.
- **Inheritance Over Composition**: Use Pydantic model inheritance to share common patterns and centralize logic.
- **Single Source of Truth**: Define base types/models once, then extend and refine them as needed.
- **Developer Experience**: Create an intuitive structure with clear import paths and well-documented fields.
- **Type Safety**: Enforce strong typing with Pydantic models for reliability and maintainability.
- **Modularity**: Keep types modular and reusable, constrained to proper modules and sub-modules to avoid circular dependencies.
- **Sane Defaults**: Provide sensible defaults via Pydantic `Field` definitions to minimize user configuration overhead.
- **Documentation**: Self-document through Pydantic model docstrings and type hints, ensuring clarity for end-users.
- **Resources and Components**: Specialize types into resource-focused (strict configurations for infrastructure entities) and component-focused (abstracting multiple resources into higher-level constructs).
- **Principle of Least Astonishment**: Ensure that types behave in predictable, intuitive ways.
- **DRY (Don't Repeat Yourself)**: Centralize common logic and fields into base models to avoid redundancy.

## Directory Structure (Type-Specific)

The directory layout encourages logical grouping and modularization of types. Each module and submodule defines its own types, ensuring easy navigation and preventing cross-module confusion.

```plaintext
modules/
├── <cloud_or_platform_name>/
│   ├── types/                   # Base and configuration types for this provider/platform
│   │   ├── __init__.py
│   │   ├── base.py              # Foundational types specific to this provider/platform
│   │   ├── config.py            # Configuration-specific type definitions
│   │   ├── metadata.py          # Metadata-related types
│   │   └── compliance.py        # Compliance-related types
├── core/
│   ├── types/                   # Core base types used across all modules
│   │   ├── __init__.py
│   │   ├── base.py              # Fundamental Pydantic base models
│   │   ├── compliance.py        # Core compliance definitions and validation
│   │   ├── config.py            # Core configuration model definitions
│   │   ├── metadata.py          # Common metadata structures
│   │   └── interfaces.py        # Interface or schema definitions for cross-module interactions
```

## Type Hierarchy

Types are organized at three levels—core, module, and submodule—each extending or specializing the previous level. This ensures consistency across different environments and allows for easy extension as complexity grows.

### Core Types

Core types establish foundational structures for resources and configurations. They define a consistent baseline, ensuring that all modules share common fields, validation rules, and patterns. Core types typically include:

- **Resource Types (Core)**: Define strict configurations for low-level, upstream resource objects with opinionated defaults.
- **Component Types (Core)**: Provide more abstracted constructs that group multiple resources into logical units with additional orchestration logic.
- **Provider Types (Core)**: Extend core types with provider-specific attributes (e.g., cloud regions, compliance labels) to facilitate multi-cloud support.

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class CommonMetadataFields(BaseModel):
    """Common metadata fields used across multiple classes."""
    tags: Dict[str, str] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)

class BaseConfigModel(BaseModel):
    """Base configuration model providing common fields."""
    enabled: bool = Field(default=False, description="Indicates if this configuration is active")
    parent: Optional[str] = Field(None, description="Identifier of the parent resource or component")
    dependencies: List[str] = Field(default_factory=list, description="List of dependencies by name or ID")
    configuration: Dict[str, object] = Field(default_factory=dict, description="Arbitrary configuration dictionary")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields, description="Common metadata fields")
```

### Module Types

Module types extend core types to incorporate module-specific configurations and logic. They are associated with a particular cloud provider, platform, or service. For example, AWS, Kubernetes, or OpenStack modules can define their own resource and component types that build upon core definitions:

- **Module Resource Types**: Add module-specific fields and validation, centralizing defaults relevant to a particular platform (e.g., AWS VPC configurations).
- **Module Component Types**: Abstract multiple related module resource types into reusable building blocks, implementing module-level orchestration logic.

```python
class NetworkConfig(BaseModel):
    """Network configuration for AWS resources."""
    vpc_cidr: str = Field(default="10.0.0.0/16", description="CIDR block for the VPC")
    subnet_cidrs: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "public": ["10.0.1.0/24", "10.0.2.0/24"],
            "private": ["10.0.3.0/24", "10.0.4.0/24"],
        },
        description="Mapping of subnet type (public/private) to CIDR ranges"
    )
    availability_zones: List[str] = Field(
        default_factory=lambda: ["us-east-1a", "us-east-1b"],
        description="List of AWS availability zones used by this network"
    )
    enable_nat_gateway: bool = Field(default=True, description="Enable NAT gateways in the public subnets")
    enable_vpn_gateway: bool = Field(default=False, description="Enable a VPN gateway for hybrid connectivity")
    enable_flow_logs: bool = Field(default=True, description="Enable VPC flow logs for observability")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields, description="Common metadata")

    @classmethod
    def validate_vpc_cidr(cls, v):
        from ipaddress import ip_network
        try:
            ip_network(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid VPC CIDR: {v}")
```

### Submodule Types

Submodule types further specialize module types by focusing on narrower subsets of functionality. For instance, within an AWS module, EKS submodule types focus exclusively on EKS cluster and node group configurations.

- **Submodule Resource Types**: Fine-grained resource definitions tailored to a submodule, such as an EKS node group or an IAM role.
- **Submodule Component Types**: Aggregate multiple submodule resource types into higher-level abstractions, representing integrated functionalities within a specific subsystem.

```python
class EksNodeGroupConfig(BaseModel):
    """Configuration for EKS node groups."""
    name: str = Field(..., description="Name of the node group")
    instance_types: List[str] = Field(
        default_factory=lambda: ["t3.medium"],
        description="EC2 instance types for the node group"
    )
    scaling_config: Dict[str, int] = Field(
        default_factory=lambda: {"desired_size": 2, "max_size": 4, "min_size": 1},
        description="Autoscaling configuration for the node group"
    )
    subnet_ids: Optional[List[str]] = Field(None, description="Optional list of subnet IDs for this node group")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields, description="Common metadata")

class EksClusterConfig(BaseModel):
    """Configuration for an EKS cluster."""
    enabled: bool = Field(default=True, description="Indicates if EKS is enabled")
    name: str = Field(..., description="Name of the EKS cluster")
    version: str = Field(default="1.29", description="EKS version")
    subnet_ids: Optional[List[str]] = Field(None, description="Subnet IDs used by the EKS cluster")
    endpoint_private_access: bool = Field(default=True, description="Enable private endpoint access")
    endpoint_public_access: bool = Field(default=True, description="Enable public endpoint access")
    node_groups: List[EksNodeGroupConfig] = Field(default_factory=list, description="Node groups for this cluster")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields, description="Common metadata")

    @classmethod
    def validate_version(cls, v):
        valid_versions = ["1.29", "1.28", "1.27", "1.26", "1.25"]
        if v not in valid_versions:
            raise ValueError(f"Invalid EKS version: {v}")
        return v
```

## Implementation Guidelines

### Type Definition

- **Naming Conventions**: Use descriptive, consistent, and readable names for models and fields.
- **Field Documentation**: Document all fields with meaningful descriptions to improve discoverability and DX.
- **Defaults**: Provide sensible defaults to streamline usage and reduce boilerplate configuration.

### Type Inheritance

- **Base Models**: Start from a core Pydantic `BaseModel` or a `BaseConfigModel` if configuration fields are required.
- **Shallow Hierarchies**: Keep inheritance chains short for simplicity and clarity.
- **Resource and Component Extensions**: Resource and component types should inherit from base models that already enforce core standards.

### Validation

- **Pydantic Validators**: Implement validators to ensure data integrity and provide helpful error messages.
- **Custom Validation**: Use custom validators for complex logic or constraints not covered by built-in types.

### Documentation

- **Model Docstrings**: Provide a class-level docstring explaining the model’s purpose.
- **Field-Level Docs**: Use `Field(description="...")` to document each field.
- **Examples**: Include example usage patterns in the documentation to guide new users.

### Export and Modularity

- **Grouping**: Group related types logically and export them through `__init__.py` files.
- **Avoid Circular Dependencies**: Keep modules self-contained and reference only what’s necessary.

## Creating New Types

Follow these steps to ensure new types integrate seamlessly into the existing hierarchy:

### 1. Define the Type’s Purpose

Decide if the type represents a resource (a low-level infrastructure entity) or a component (an abstraction composed of multiple resources). If needed, determine if it’s a provider-specific, module, or submodule type.

### 2. Extend Existing Types

Identify the appropriate base model:

- Start with `BaseModel` or `BaseConfigModel` from core types.
- For provider-specific logic, extend a relevant provider or module-specific base type.
- Build upon submodule types if you’re adding more granular domain-specific functionality.

### 3. Add Custom Fields

- Provide meaningful names, docstrings, and defaults.
- Validate fields where necessary to ensure correctness and safety.

### 4. Document the Type

- Explain the type’s purpose and usage context.
- Include field-level descriptions and examples.

### Example: Defining a New Type

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class MyCustomResource(BaseModel):
    """Custom resource representing a hypothetical infrastructure entity."""
    name: str = Field(..., description="Unique name of the custom resource")
    custom_field: str = Field(default="default_value", description="A custom field with a default value")
    optional_field: Optional[int] = Field(None, description="An optional integer field")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields, description="Common metadata")

class MyCustomComponent(BaseModel):
    """Abstracted component representing a collection of resources."""
    name: str = Field(..., description="Name of the component")
    resource_list: List[str] = Field(default_factory=list, description="List of resource identifiers")
    logic_flag: bool = Field(default=True, description="Flag controlling component logic")
    metadata: CommonMetadataFields = Field(default_factory=CommonMetadataFields, description="Common metadata")
```

### 5. Test and Validate

- Write tests to confirm default behaviors.
- Validate that custom validators raise appropriate errors for invalid input.

### 6. Export the Type

- Add your new types to the `__init__.py` file of the appropriate directory.
- Ensure they are accessible to other parts of the codebase.

## Best Practices

1. **Clear Separation**: Keep resource-focused and component-focused types distinct, while giving each a well-defined purpose.
2. **Comprehensive Documentation**: Document all types and fields clearly so developers can quickly understand and use them.
3. **Meaningful Defaults**: Leverage defaults to reduce overhead on users, guiding them toward best practices effortlessly.
4. **Maintainability and Readability**: Prioritize code clarity and logical organization to simplify onboarding and long-term maintenance.
