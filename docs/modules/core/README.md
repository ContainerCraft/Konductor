# Konductor Core Module

The **Konductor Core Module** provides the foundational, provider-agnostic framework for Konductor's Infrastructure as Code (IaC) platform. By establishing standardized data models, compliance configurations, metadata handling, and lifecycle patterns, the core module ensures that all other modules—whether targeting AWS, GCP, Azure, OpenStack, Kubernetes, or any other platform—operate within a consistent, secure, and maintainable ecosystem.

This README provides a high-level overview of the core module’s purpose, architecture, and integration points. For detailed type definitions and low-level technical references, please consult the [Types Documentation](./TYPES.md).

## Table of Contents

1. [Introduction](#introduction)
2. [Purpose and Scope](#purpose-and-scope)
3. [Core Principles](#core-principles)
4. [Provider-Agnostic and Unified Interface](#provider-agnostic-and-unified-interface)
5. [Foundational Data Models and Patterns](#foundational-data-models-and-patterns)
6. [Compliance and Security](#compliance-and-security)
7. [Global Metadata Management](#global-metadata-management)
8. [Module Integration and Interfaces](#module-integration-and-interfaces)
9. [Configuration Management](#configuration-management)
10. [Extensibility and Modularity](#extensibility-and-modularity)
11. [Usage Guidelines](#usage-guidelines)
12. [Related Documentation](#related-documentation)
13. [Conclusion](#conclusion)

## Introduction

Modern, multi-cloud IaC environments demand consistent, secure, and compliant patterns. The Konductor Core Module addresses these needs by serving as the backbone of the entire IaC codebase. Through a well-defined set of Pydantic models, strict typing, runtime validation, and DRY design principles, the core module ensures that all modules—regardless of the provider or technology—adhere to a unified standard of quality, compliance, and maintainability.

## Purpose and Scope

**What the Core Module Does:**

- Defines fundamental Pydantic-based data models and protocols for resources, configurations, compliance, and deployment results.
- Provides a uniform abstraction for all providers and modules, ensuring consistent tagging, labeling, annotations, compliance checks, and lifecycle management.
- Offers integrated compliance frameworks (FISMA, NIST) and ATO enforcement at the foundational level, ensuring production stacks meet stringent requirements.
- Introduces shared base classes and metadata fields (e.g., `CommonMetadataFields`) to keep the code DRY, easier to maintain, and more coherent.

**What It Does Not Do:**

- The core module does not implement provider-specific logic. Instead, it establishes universal standards for all modules to follow.
- It does not impose project-specific application logic. Instead, it provides flexible building blocks that specialized modules can extend.

## Core Principles

1. **Provider-Agnostic**: No assumptions about specific cloud providers. AWS, GCP, Azure, OpenStack, Kubernetes, and beyond integrate seamlessly.
2. **Strict Typing and Runtime Validation**: Fully Pydantic-based models ensure early detection of misconfigurations and adherence to schemas at runtime.
3. **Security and Compliance Embedded**: Compliance models (FISMA, NIST, ATO) are integrated at the core, ensuring production stacks cannot bypass essential authorization and lifecycle controls.
4. **DRY and Maintainable**: Common fields (like `metadata`) and patterns (like `enabled` states) are centralized, reducing duplication and making the codebase more maintainable.
5. **Pulumi-Native Integration**: Designed to align with Pulumi stack patterns, ensuring smooth configuration loading, state management, and resource orchestration.

## Provider-Agnostic and Unified Interface

By defining universal interfaces (`ModuleInterface`, `DeploymentContext`) and standardized configuration patterns, the core module creates a single "language" all modules speak. This ensures:

- Every module follows the same lifecycle steps (validate, deploy, handle dependencies).
- Every resource benefits from consistent metadata and compliance checks.
- Teams can integrate new providers easily without re-engineering fundamental IaC patterns.

A unified interface leads to a consistent development experience, simpler onboarding, and more predictable deployments.

## Foundational Data Models and Patterns

Key elements:

- **`CommonMetadataFields`**: A central model for tags, labels, and annotations, ensuring uniform metadata application.
- **`BaseConfigModel`**: A shared base class providing common fields (`enabled`, `dependencies`, `configuration`, `metadata`) for all configuration models.
- **`InitializationConfig`**: Augments `BaseConfigModel` with stack/project details, compliance configs, and Git metadata.
- **`ResourceModel`**: A standardized resource representation, including timestamps and metadata.
- **`ComplianceConfig`, `FismaConfig`, `NistConfig`**: Models that ensure production environments meet required authorization and controls.

These common elements reduce complexity and enforce coherence across the entire IaC stack.

## Compliance and Security

Compliance is integral to the core module:

- **ATO Enforcement**: Production stacks must specify authorized and eol dates.
- **FISMA/NIST Controls**: Centralized compliance models prevent ad-hoc logic and ensure consistent enforcement.
- **Consistent Validation**: Pydantic validation catches invalid compliance configurations early, reducing risk and audit overhead.

## Global Metadata Management

Global metadata is managed via `MetadataSingleton`:

- **Global Tags, Labels, Annotations**: Set once, apply everywhere.
- **Git Metadata**: Resources traceable to a specific commit or tag.
- **Consistent Application**: `setup_global_metadata()` ensures a single source of truth.

This empowers governance, compliance, and platform-wide observability at scale.

## Module Integration and Interfaces

`ModuleInterface` and `DeploymentContext` define how modules interact:

- **ModuleInterface**: Modules must implement `validate()`, `deploy()`, `dependencies()` uniformly.
- **DeploymentContext**: Provides a consistent environment for retrieving configurations and performing deployments.

This uniform interface simplifies maintenance, testing, and integrating new modules, regardless of the underlying provider.

## Configuration Management

`ConfigManager` centralizes loading and caching Pulumi configurations:

- **Unified Config Access**: Modules load configurations from a single, consistent source.
- **Validation-First**: Pydantic ensures that misconfigurations never proceed undetected.
- **Dynamic, Layered Configs**: Override defaults and adapt to different environments without code duplication.

This leads to more reliable and predictable IaC workflows.

## Extensibility and Modularity

By focusing on provider-agnostic abstractions and DRY patterns:

- **Easy Provider Onboarding**: Adding a new provider requires conforming to defined interfaces and models, not reinventing patterns.
- **Scalable and Future-Ready**: As new technologies or compliance frameworks appear, integrating them is straightforward with stable, universal standards.

The result is a codebase that evolves gracefully as infrastructure needs change.

## Usage Guidelines

- **Validate Early**: Use `ComplianceConfig.from_pulumi_config()` and Pydantic validations to prevent invalid deployments.
- **Use Common Models**: Apply `CommonMetadataFields` to ensure consistent tagging and labeling.
- **Implement Protocols**: Follow `ModuleInterface` and `DeploymentContext` for uniform, testable module structures.
- **Centralize Compliance**: Rely on `ComplianceConfig` for production authorization and controls.
- **Global Metadata Once**: Use `setup_global_metadata()` and `MetadataSingleton` to achieve consistent metadata across the platform.

## Related Documentation

- [Core Module Types Detailed Reference (TYPES.md)](./TYPES.md)
- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Development Standards](../developer_guide/pulumi-python.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)

## Conclusion

The Konductor Core Module establishes a robust, provider-agnostic foundation for building, scaling, and governing IaC deployments. By moving entirely to Pydantic models, we gain runtime validation, richer schemas, and DRY patterns, ensuring a more maintainable, secure, and consistent environment as Konductor evolves.

With these stable standards in place, integrating new providers, applying compliance frameworks, and managing infrastructure remains straightforward, predictable, and aligned with the highest quality standards.
