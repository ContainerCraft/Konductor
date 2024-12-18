# Core Module Types (revision08)

Welcome to the **Core Module Types** reference. This document provides a detailed explanation of the `core/types` module after the DRY-focused refactoring (revision08). The refactoring introduces common models to reduce duplication and clarifies responsibilities of each class and interface. These types serve as the foundational building blocks for Konductor's Infrastructure as Code (IaC) environment, ensuring consistency, security, compliance, and maintainability.

This guide is suitable for engineers at all levels. By understanding these core types, you can design, implement, and extend Konductor IaC confidently, leveraging Pulumi's capabilities and industry best practices.

## Table of Contents

1. [Introduction](#introduction)
2. [Core Principles and Conventions](#core-principles-and-conventions)
3. [Exceptions](#exceptions)
4. [Metadata Models](#metadata-models)
   - [CommonMetadataFields](#commonmetadatafields)
   - [GitInfo](#gitinfo)
5. [Compliance and Configuration Models](#compliance-and-configuration-models)
   - [OwnershipInfo, AtoConfig, ProjectOwnership](#ownershipinfo-atoconfig-projectownership)
   - [StackConfig (Compliance Project)](#stackconfig-compliance-project)
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
    - [StackConfig for Outputs](#stackconfig-for-outputs)
    - [StackOutputs](#stackoutputs)
    - [ModuleDefaults](#moduledefaults)
11. [Best Practices and Usage Guidelines](#best-practices-and-usage-guidelines)
12. [Conclusion](#conclusion)
13. [Related Documentation](#related-documentation)

## Introduction

The `core/types` module defines a set of Pydantic models, TypedDicts, and Protocols that establish the core schema for configuration, compliance, resource metadata, and module lifecycle in Konductor's Pulumi-based IaC environment. This revision08 focuses on a DRY approach, reducing redundancy and consolidating common attributes into reusable models.

## Core Principles and Conventions

- **Strict Typing**: All models use strict typing, leveraging Pydantic and TypedDict for validation and clarity.
- **Pulumi Alignment**: Models and interfaces integrate smoothly with Pulumi stack configurations and resource management patterns.
- **Compliance and Security**: Compliance configurations (FISMA, NIST, ATO) are central. Production deployments enforce stricter requirements.
- **DRY and Maintainable**: Common fields (e.g., tags, labels, annotations) and patterns (e.g., enabling/disabling modules) are factored into shared base models.
- **No Hardcoded Secrets**: All sensitive data must be handled securely outside the code or through Pulumi secrets.

## Exceptions

- **CoreError**: Base exception for the core module.
- **ModuleLoadError**: Raised if a module cannot be loaded, aiding in clear error reporting and debugging.

## Metadata Models

### CommonMetadataFields

**Class:** `CommonMetadataFields`
Provides `tags`, `labels`, and `annotations` fields reused across various models, ensuring uniform application of metadata.

### GitInfo

**Class:** `GitInfo`
Captures essential Git repository metadata (commit, branch, remote, optional release tag) at deployment time, allowing traceability of deployed code versions.

## Compliance and Configuration Models

### OwnershipInfo, AtoConfig, ProjectOwnership

- **OwnershipInfo** and **ProjectOwnership**: TypedDict structures defining contact and ownership details.
- **AtoConfig**: Includes `authorized`, `eol`, and `last_touch` timestamps for production environments, ensuring no unapproved deployments.

### StackConfig (Compliance Project)

**Class:** `StackConfig` (within ComplianceConfig)
Represents the project's environment configuration, production flags, ownership details, and ATO configuration. This ensures environment-specific compliance and governance.

### FismaConfig and NistConfig

**Classes:** `FismaConfig`, `NistConfig`
Describe compliance levels and modes for FISMA and NIST frameworks. Enable or disable controls and handle exceptions. Together, they guide compliance-enforcing logic in the IaC pipelines.

### ComplianceConfig

**Class:** `ComplianceConfig`
Holds the combined `StackConfig`, `FismaConfig`, and `NistConfig`. Provides a `from_pulumi_config()` method to build configurations directly from Pulumi stack data. If production, authorized/eol must be present; otherwise defaults apply.

### BaseConfigModel

**Class:** `BaseConfigModel`
A base configuration model providing:
- `enabled`: Whether a module or configuration set is active
- `parent`: Parent module or resource reference
- `dependencies`: A list of module dependencies
- `configuration`: Arbitrary config dictionaries
- `metadata`: `CommonMetadataFields` for consistent tagging and labeling

This base class minimizes duplication across various config models.

### InitializationConfig

**Class:** `InitializationConfig`
Extends `BaseConfigModel` with:
- `pulumi_config`: Pulumi configuration
- `stack_name`, `project_name`: Identifiers for stack and project
- `global_depends_on`: Global resource dependencies
- `git_info`: Git metadata
- `compliance_config`: Compliance settings
- `deployment_date_time`, `deployment_manager`: Deployment context details

This ensures the core module initialization has all required info before any module deployments.

### ModuleRegistry and ModuleBase

**Classes:** `ModuleRegistry`, `ModuleBase`
`ModuleRegistry` adds a required `name` field.
`ModuleBase` defines a standard pattern for modules, ensuring `name`, `enabled`, `dependencies`, and `metadata` are uniformly managed.

## Resource and Deployment Models

### ResourceModel

**Class:** `ResourceModel`
Represents a resource with:
- `name`
- `metadata` (via `CommonMetadataFields`)
- `created_at`, `updated_at` timestamps

This simplifies resource representation, ensuring that all resources follow a consistent metadata pattern.

### ModuleDeploymentResult

**Class:** `ModuleDeploymentResult`
Captures outcomes of a module deployment:
- `config`: `ResourceModel` instances representing deployed configurations
- `compliance`: Compliance/tracing info
- `errors`: Any errors encountered
- `metadata`: Additional deployment-level metadata

This helps clients and consumers understand what changed during deployment, what compliance context applies, and any encountered issues.

## Interfaces and Protocols

### DeploymentContext

**Protocol:** `DeploymentContext`
Defines the interface for executing deployments and retrieving the configuration model. This ensures modules can be deployed in a consistent manner regardless of underlying logic.

### ModuleInterface

**Protocol:** `ModuleInterface`
Defines minimal lifecycle methods for a module:
- `validate()`: Validate its configuration
- `deploy(ctx)`: Deploy using the given context
- `dependencies()`: Declare module dependencies

This common interface ensures a uniform pattern across all modules, simplifying integration and testing.

## Global Metadata Management

### MetadataSingleton

**Class:** `MetadataSingleton`
A thread-safe singleton providing a global store for tags, labels, annotations, and git metadata. `setup_global_metadata(init_config)` uses this to populate global metadata once, ensuring a single source of truth.

### InitConfig Protocol and setup_global_metadata()

**Protocol:** `InitConfig`
Defines `project_name`, `stack_name`, `git_info`, and `metadata` needed to set global metadata.
**Function:** `setup_global_metadata(init_config)`
Merges provided metadata with git and project info, populating the `MetadataSingleton`.

## Configuration Management Utilities

### ConfigManager

**Class:** `ConfigManager`
Handles loading and caching of Pulumi configuration:
- `get_config()`: Loads full stack config.
- `get_module_config(module_name)`: Retrieves a module's config.
- `get_enabled_modules()`: Lists modules that are enabled.

By centralizing config retrieval, `ConfigManager` reduces repeated code and improves maintainability.

## Stack-Level Types

### GlobalMetadata

**Class:** `GlobalMetadata`
Represents global tags, labels, and annotations at the stack level. Supports platform-wide governance by applying consistent metadata.

### SourceRepository

**Class:** `SourceRepository`
Holds branch, commit, and remote URL (and optional tag) for auditing and rollback capabilities. Integrates with compliance and metadata to ensure full traceability of deployed code.

### StackConfig for Outputs

**Note:** There are now two `StackConfig` concepts. One inside `ComplianceConfig.project` (representing compliance project environment), and one at the stack outputs level. For clarity:
- `ComplianceConfig.project` uses `StackConfig` to define environment and ATO details.
- `StackConfig` at the outputs level holds `compliance`, `metadata`, `source_repository`.

This naming can be adjusted if desired. As is, it differentiates project compliance config (internal) from the top-level stack outputs `StackConfig`.

### StackOutputs

**Class:** `StackOutputs`
Combines:
- `stack`: A `StackConfig` with compliance, metadata, and source repository details
- `secrets`: Optional sensitive data

This final aggregation can be shared with other systems or teams.

### ModuleDefaults

**Class:** `ModuleDefaults`
Defines a baseline configuration (e.g., `enabled`, `config`) that modules can inherit. Ensures new modules have a consistent starting point.

## Best Practices and Usage Guidelines

- **Validate Early**: Use `from_pulumi_config()` methods and Pydantic validation to prevent malformed deployments.
- **Embrace Common Models**: Leverage `CommonMetadataFields` to avoid duplicating metadata fields across models.
- **Stick to Protocols**: Implement `ModuleInterface` and use `DeploymentContext` to ensure modules are deployable in a uniform manner.
- **Centralize Compliance**: Maintain compliance via `ComplianceConfig`, ensuring production stacks meet authorization and expiration requirements.
- **Utilize `MetadataSingleton`**: Set global metadata once, ensuring a single, authoritative source for tagging and labeling.

## Conclusion

The revision08 `core/types` module presents a cleaner, DRY, and more maintainable type system for Konductor IaC. By consolidating common fields, standardizing compliance and resource models, and leveraging protocols for modules and deployment contexts, this approach ensures a robust foundation that scales with complexity and supports multi-cloud environments gracefully.

Through these models, teams can confidently manage infrastructure configurations, apply compliance and metadata consistently, and integrate smoothly with Pulumi and other modules.

## Related Documentation

- [Developer Guide](../developer_guide/README.md)
- [Pulumi Python Development Standards (pulumi-python.md)](../developer_guide/pulumi-python.md)
- [Types Hierarchy Guide](../developer_guide/Types_Hierarchy.md)
- [Documentation Style Guide](../developer_guide/documentation.md)
- [Contribution Guidelines](../contribution_guidelines.md)
