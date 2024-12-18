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

Modern, multi-cloud IaC environments demand consistent, secure, and compliant patterns. The Konductor Core Module addresses these needs by serving as the backbone of the entire IaC codebase. Through a well-defined set of Pydantic models, typed configurations, protocols, and DRY design, the core module ensures that all modules—no matter what provider or technology they manage—adhere to a unified standard of quality, compliance, and maintainability.

## Purpose and Scope

**What the Core Module Does:**

- Defines fundamental data models and protocols for resources, configurations, compliance, and deployment results.
- Provides a uniform abstraction for all providers and modules, ensuring consistent tagging, labeling, annotations, compliance checks, and lifecycle management.
- Offers compliance frameworks (FISMA, NIST) and ATO enforcement integrated at the foundational level.
- Introduces shared base classes and metadata fields (e.g., `CommonMetadataFields`) to promote a DRY codebase.

**What It Does Not Do:**

- The core module does not implement provider-specific logic. Instead, it sets universal standards.
- It does not impose project-specific logic. Instead, it provides building blocks for more specialized modules to leverage.

## Core Principles

1. **Provider-Agnostic**: The core module never assumes a particular provider. It ensures AWS, GCP, Azure, OpenStack, Kubernetes, and beyond can integrate seamlessly.
2. **Strict Typing and Validation**: Pydantic models and typed dictionaries guarantee correctness and clarity. Early validation prevents runtime misconfigurations.
3. **Security and Compliance Embedded**: Compliance-oriented fields (FISMA, NIST, ATO) are baked in, ensuring production stacks meet stringent requirements.
4. **DRY and Maintainable**: Common fields and patterns (e.g., metadata, enabled/disabled states) are factored into shared base classes, reducing duplication.
5. **Pulumi-Native Integration**: Patterns and interfaces align with Pulumi’s stack-based workflows, ensuring smooth integration and state management.

## Provider-Agnostic and Unified Interface

By defining universal interfaces (`ModuleInterface`, `DeploymentContext`) and standardized configuration patterns, the core module creates a single “language” that all modules speak. This ensures:

- Every module follows the same lifecycle hooks (validate, deploy, manage dependencies).
- Every resource is enriched with consistent metadata and compliance checks.
- Teams can integrate new providers without rethinking foundational IaC patterns.

The result is a uniform development experience, simpler onboarding, and more predictable deployments.

## Foundational Data Models and Patterns

Key patterns include:

- **`CommonMetadataFields`**: A central model for tags, labels, annotations, ensuring consistent metadata application.
- **`BaseConfigModel`**: A shared base class for configuration, providing `enabled`, `dependencies`, `configuration`, and `metadata`.
- **`InitializationConfig`**: Augments `BaseConfigModel` with stack/project details, compliance, and git metadata.
- **`ResourceModel`**: A unified resource representation including `metadata` and timestamps.
- **`ComplianceConfig`, `FismaConfig`, `NistConfig`**: Compliance models to ensure production environments meet authorization and controls requirements.

By consolidating these common elements, the core module reduces complexity and ensures a cohesive experience across the entire IaC codebase.

## Compliance and Security

Compliance is not optional. The core module integrates compliance configurations at the base level, ensuring:

- **ATO Enforcement**: Production stacks must provide authorized and eol dates.
- **FISMA/NIST Integration**: Controls, modes, and exceptions are captured in a single compliance model, preventing ad-hoc compliance logic.
- **Consistent Compliance Checks**: Modules and deployments inherit these patterns automatically, reducing risk and audit overhead.

## Global Metadata Management

Global metadata is managed via a thread-safe `MetadataSingleton`:

- **Global Tags, Labels, Annotations**: Applied once and inherited universally.
- **Git Metadata**: Every resource can trace its lineage back to a specific commit or tag.
- **Consistent Application**: `setup_global_metadata()` ensures a single, authoritative source for all metadata.

This approach enables governance, compliance, and observability at scale.

## Module Integration and Interfaces

**`ModuleInterface`** and **`DeploymentContext`** define how modules interact:

- **ModuleInterface**: Requires `validate()`, `deploy()`, and `dependencies()` methods, ensuring all modules follow a known lifecycle pattern.
- **DeploymentContext**: Provides a consistent deployment environment, retrieving configurations and executing deployments in a predictable manner.

This uniform interface simplifies maintenance, testing, and extensibility across providers and technologies.

## Configuration Management

**`ConfigManager`** centralizes configuration loading and caching:

- **Unified Config Access**: Modules request their configurations from a single source.
- **Layered and Overridden Configs**: Stacks can override defaults, and modules can adapt dynamically.
- **Early Validation**: Pydantic ensures invalid configurations never reach runtime deployments.

This reduces duplication and errors, increasing reliability of the IaC workflows.

## Extensibility and Modularity

By focusing on provider-agnostic abstractions and DRY models:

- **Easy Provider Onboarding**: Adding a new provider module only requires conforming to the defined interfaces and base models.
- **Scalable and Future-Ready**: As new technologies or compliance frameworks emerge, integrating them is straightforward since the core sets stable standards.

This approach ensures that Konductor can evolve gracefully as infrastructure needs change.

## Usage Guidelines

- **Validate Early**: Leverage `ComplianceConfig.from_pulumi_config()` and Pydantic validations to catch configuration issues before deployments begin.
- **Use Common Models**: Apply `CommonMetadataFields` to ensure consistent tagging and labeling practices.
- **Implement Protocols**: Adhere to `ModuleInterface` and `DeploymentContext` for a uniform, testable, and maintainable module structure.
- **Manage Compliance Centrally**: Rely on `ComplianceConfig` to enforce production requirements and maintain a single source of compliance truth.
- **Global Metadata Once**: Use `setup_global_metadata()` and `MetadataSingleton` to ensure consistent metadata across the entire platform.

## Related Documentation

- [Core Module Types Detailed Reference (TYPES.md)](./TYPES.md)
- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Development Standards](../developer_guide/pulumi-python.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)

## Conclusion

The Konductor Core Module establishes a robust, provider-agnostic foundation for building, scaling, and governing IaC deployments. By consolidating metadata management, compliance enforcement, resource modeling, and configuration standardization into a single framework, the core module transforms a complex multi-cloud environment into a uniform, secure, and maintainable platform.

As Konductor evolves, the core module’s DRY patterns and consistent interfaces ensure that integrating new providers, applying compliance frameworks, and managing infrastructure remains straightforward and predictable, supporting the platform’s adaptability and future readiness.
