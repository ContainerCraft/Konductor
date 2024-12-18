# Core Module Types (revision10)

Welcome to the **Core Module Types** reference. This document provides a detailed, technical explanation of the `core/types` module after the comprehensive Pydantic-only refactoring (revision10). In this iteration, all data structures previously defined with `TypedDict` have been replaced by Pydantic models, ensuring runtime validation, consistency, and richer modeling capabilities. This approach maintains the project's DRY principles, strict typing, and compliance/security integration, while enhancing the overall resilience and clarity of the type system.

This guide is suitable for engineers at all levels. By understanding these pure Pydantic models and interfaces, you can design, implement, and extend Konductor IaC confidently, leveraging Pulumi and industry best practices for stable, secure, and compliant infrastructure deployments.

## Table of Contents

1. [Introduction](#introduction)
2. [Core Principles and Conventions](#core-principles-and-conventions)
3. [Exceptions](#exceptions)
4. [Metadata Models](#metadata-models)
   - [CommonMetadataFields](#commonmetadatafields)
   - [GitInfo](#gitinfo)
5. [Compliance and Configuration Models](#compliance-and-configuration-models)
   - [OwnershipInfo, AtoConfig, ProjectOwnership](#ownershipinfo-atoconfig-projectownership)
   - [ScipConfig (Project Compliance)](#scipconfig-project-compliance)
   - [FismaConfig and NistConfig](#fismaconfig-and-nistconfig)
   - [ComplianceConfig](#complianceconfig)
   - [BaseConfigModel](#baseconfigmodel)
   - [InitializationConfig](#initializationconfig)
   - [ModuleRegistry and ModuleBase](#moduleregistry-and-modulebase)
6. [Resource and Deployment Models](#resource-and-deployment-models)
   - [ResourceModel](#resourcemodel)
   - [ModuleDeploymentResult](#moduledeploymentresult)
7. [Interfaces and Protocols](#interfaces-and-protocols)
   - [DeploymentContext](#deploymentcontext)
   - [ModuleInterface](#moduleinterface)
8. [Global Metadata Management](#global-metadata-management)
   - [MetadataSingleton](#metadatasingleton)
   - [InitConfig Protocol and setup_global_metadata()](#initconfig-protocol-and-setup_global_metadata)
9. [Configuration Management Utilities](#configuration-management-utilities)
   - [ConfigManager](#configmanager)
10. [Stack-Level Types](#stack-level-types)
    - [GlobalMetadata](#globalmetadata)
    - [SourceRepository](#sourcerepository)
    - [StackConfig](#stackconfig)
    - [StackOutputs](#stackoutputs)
    - [ModuleDefaults](#moduledefaults)
11. [Best Practices and Usage Guidelines](#best-practices-and-usage-guidelines)
12. [Conclusion](#conclusion)
13. [Related Documentation](#related-documentation)

## Introduction

In revision10, the `core/types` module adopts a fully Pydantic-based approach, eliminating all `TypedDict` usages. This choice strengthens runtime validation, ensures uniform schema definitions, and enables advanced Pydantic features (defaults, validators, type coercion) across all data models. The result is a more robust, consistent, and maintainable type system that fully aligns with Pulumi’s stack-based IaC workflows and Konductor’s compliance and security mandates.

## Core Principles and Conventions

- **Strict Typing and Runtime Validation**: All models are Pydantic-based, providing runtime checks that catch invalid data early.
- **Pulumi-Native Alignment**: Patterns and interfaces mesh seamlessly with Pulumi stacks, ensuring consistent configuration, resource modeling, and lifecycle management.
- **Compliance and Security-First**: Models like `ComplianceConfig`, `FismaConfig`, and `NistConfig` ensure production stacks meet FISMA/NIST controls and ATO requirements out of the box.
- **DRY and Maintainable**: Common patterns—such as resource metadata and enabling/disabling modules—are encapsulated in shared base classes (e.g., `BaseConfigModel`).
- **No Hardcoded Secrets**: All sensitive data remains outside the code or handled via Pulumi secrets, following security best practices.

## Exceptions

- **CoreError**: The base exception for the core module, providing a foundation for more specific errors.
- **ModuleLoadError**: Raised when a module cannot be loaded, aiding in diagnosing configuration or dependency issues clearly.

## Metadata Models

### CommonMetadataFields

**Class:** `CommonMetadataFields`
Centralizes `tags`, `labels`, and `annotations`, ensuring every resource or configuration that requires metadata can use a common schema. This simplifies the propagation of governance, compliance, and organizational metadata across the entire IaC estate.

### GitInfo

**Class:** `GitInfo`
Captures repository commit hash, branch name, remote URL, and optional release tag. Tracing infrastructure changes back to specific code commits or release tags becomes effortless, improving auditability and helping with rollbacks or debugging.

## Compliance and Configuration Models

### OwnershipInfo, AtoConfig, ProjectOwnership

All previously `TypedDict`-based structures are now Pydantic models:

- **OwnershipInfo**: Defines contact details for project owners or teams.
- **AtoConfig**: Specifies Authority to Operate dates (authorized, end-of-life), critical for production compliance.
- **ProjectOwnership**: Bundles `OwnershipInfo` for both owner and operations, ensuring that accountability and escalation paths are clearly documented.

### ScipConfig (Project Compliance)

**Class:** `ScipConfig`
Represents project-specific compliance settings:
- `environment` and `production` fields mark which environment and whether it’s production.
- `ownership` and `ato` fields enforce that production stacks must have explicit authorization.

### FismaConfig and NistConfig

**Classes:** `FismaConfig`, `NistConfig`
These classes define compliance levels and exceptions for FISMA and NIST controls. Pydantic ensures that invalid compliance configurations never reach runtime deployments.

### ComplianceConfig

**Class:** `ComplianceConfig`
Consolidates `ScipConfig` (project details), `FismaConfig`, and `NistConfig`.
`from_pulumi_config()` enables runtime construction from Pulumi stack configs. Production stacks are validated to ensure authorized and eol dates are present, preventing non-compliant deployments.

### BaseConfigModel

**Class:** `BaseConfigModel`
A fundamental building block providing common fields: `enabled`, `parent`, `dependencies`, `configuration`, and `metadata`. Using `CommonMetadataFields` and `BaseConfigModel` ensures all modules and configurations follow a consistent pattern.

### InitializationConfig

**Class:** `InitializationConfig`
Extends `BaseConfigModel` to handle stack/project initialization details, compliance config, Git info, and other essential fields (`pulumi_config`, `stack_name`, `project_name`). This ensures that the core module has all necessary context before modules are deployed.

### ModuleRegistry and ModuleBase

**Classes:** `ModuleRegistry`, `ModuleBase`
`ModuleRegistry` introduces a `name` field for identifying modules.
`ModuleBase` inherits from `BaseConfigModel` and enforces a `name` field, representing a deployable module. Together, they define a standard interface and lifecycle pattern for all modules.

## Resource and Deployment Models

### ResourceModel

**Class:** `ResourceModel`
Represents a resource with `name`, `metadata`, and timestamps (`created_at`, `updated_at`). This standardized model ensures that all resources share a uniform metadata structure and are traceable through time.

### ModuleDeploymentResult

**Class:** `ModuleDeploymentResult`
Captures the outcome of a module deployment:
- `config`: List of `ResourceModel` instances for the deployed resources or configurations.
- `compliance`: Compliance/tracing information.
- `errors`: Issues encountered during deployment.
- `metadata`: Additional deployment-level metadata.

This provides a clear, consistent return value for module deployments, aiding in diagnostics and auditing.

## Interfaces and Protocols

### DeploymentContext

**Protocol:** `DeploymentContext`
Defines how the deployment environment provides configurations and executes deployments.
`get_config()` returns the configuration model, and `deploy()` initiates the deployment, returning a `ModuleDeploymentResult`.

### ModuleInterface

**Protocol:** `ModuleInterface`
Specifies that modules must implement:
- `validate(config)`: Check configuration correctness.
- `deploy(ctx)`: Perform the deployment using `DeploymentContext`.
- `dependencies()`: Declare dependencies on other modules.

This ensures a consistent lifecycle for all modules, irrespective of the provider or service they manage.

## Global Metadata Management

### MetadataSingleton

**Class:** `MetadataSingleton`
A thread-safe singleton that holds global tags, labels, annotations, and Git metadata. Once set, these metadata fields are uniformly available to all modules and resources, ensuring governance and compliance data is globally consistent.

### InitConfig Protocol and setup_global_metadata()

**Protocol:** `InitConfig`
Defines required fields (`project_name`, `stack_name`, `git_info`, `metadata`) needed for global metadata setup.

**Function:** `setup_global_metadata(init_config)`
Merges global metadata and Git info into the `MetadataSingleton`, ensuring all resources and modules share a consistent global metadata context from the start.

## Configuration Management Utilities

### ConfigManager

**Class:** `ConfigManager`
Centralizes configuration loading:
- `get_config()`: Retrieves the entire stack config once, caching results.
- `get_module_config()`: Extracts a specific module’s configuration.
- `get_enabled_modules()`: Identifies which modules have `enabled: true`.

Unified config management reduces code duplication and improves reliability.

## Stack-Level Types

### GlobalMetadata

**Class:** `GlobalMetadata`
Stores global tags, labels, and annotations at the stack level. This ensures that platform-wide governance and compliance tags are consistently applied to all resources and configurations.

### SourceRepository

**Class:** `SourceRepository`
Holds branch, commit, remote, and optional tag for the source repository. This makes it easy to correlate deployed infrastructure with a specific code commit or release, improving traceability.

### StackConfig

**Class:** `StackConfig`
Combines `compliance` (via `ComplianceConfig`), `metadata` (`GlobalMetadata`), and `source_repository` details into a coherent top-level model representing the entire stack’s configuration.

### StackOutputs

**Class:** `StackOutputs`
Aggregates `StackConfig` and optional `secrets` into a final output model. This can be shared with other teams or pipelines, providing a complete view of the stack’s final state and compliance posture.

### ModuleDefaults

**Class:** `ModuleDefaults`
Provides a baseline configuration for modules (`enabled`, `config`). New modules can start from these defaults, ensuring a consistent initial configuration across the platform.

## Best Practices and Usage Guidelines

- **Validate Early**: Use `ComplianceConfig.from_pulumi_config()` and Pydantic validation to catch issues before deployments start.
- **Embrace Common Models**: `CommonMetadataFields` and `BaseConfigModel` reduce code duplication and ensure consistent patterns.
- **Implement Protocols**: Following `ModuleInterface` and `DeploymentContext` yields a uniform, testable, and maintainable module ecosystem.
- **Enforce Compliance Centrally**: `ComplianceConfig` guarantees that production stacks meet authorization and control requirements.
- **Set Metadata Once**: Use `setup_global_metadata()` and `MetadataSingleton` for a single authoritative source of metadata.

## Conclusion

With revision10, the `core/types` module fully adopts Pydantic-based models, enhancing runtime validation, consistency, and extensibility. The removal of TypedDicts clarifies schemas, while the established patterns continue to ensure a robust, secure, and maintainable IaC foundation.

Armed with these models and interfaces, teams can confidently manage complex, multi-cloud environments, enforce compliance uniformly, and integrate new providers or compliance frameworks with minimal friction—ensuring Konductor’s future-readiness in a rapidly evolving infrastructure landscape.

## Related Documentation

- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Development Standards (pulumi-python.md)](../developer_guide/pulumi-python.md)
- [Types Hierarchy Guide](../developer_guide/Types_Hierarchy.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)
