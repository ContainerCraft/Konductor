# Next Generation Architecture Design

## 1. Introduction

This document outlines the next generation architecture for our Infrastructure as Code (IaC) framework built with Pulumi using Python. The architecture fully embraces the provider-resource-component model, enabling stronger encapsulation, improved reusability, and more consistent enforcement of organizational standards.

Our approach is fundamentally declarative and state-driven, leveraging Pulumi's native capabilities for state management and resource lifecycle handling. Infrastructure is defined as desired state in code, and Pulumi's engine handles the reconciliation, diffing, and resource tracking automatically. This aligns our framework with modern declarative IaC tools like Terraform, CloudFormation, and Bicep, while adding the flexibility and power of a full programming language.

**Component Resource Pattern**: From the outset, we are adopting Pulumi's ComponentResource pattern as our primary abstraction mechanism. This allows us to create higher-level, reusable building blocks that encapsulate cloud resources into logical groups. By implementing the Component Resource pattern from the beginning, we establish a foundation for maintainable, modular infrastructure code that will scale with our needs without requiring future refactoring.

### 1.1 Purpose

The purpose of this redesign is to address limitations in the current architecture while enhancing:

- **Modularity**: Cleaner separation of concerns and improved component reusability
- **Maintainability**: Reduced complexity through composition over inheritance
- **Extensibility**: Easier addition of new providers and resources
- **Compliance**: Consistent enforcement of organizational standards
- **Type Safety**: Improved static type checking and IDE support
- **Abstraction**: Encapsulation of implementation details through Component Resources

### 1.2 Core Design Principles

The refactored architecture embodies key software engineering principles:

- **Composition Over Inheritance**: Resource components are primarily composed, reducing inheritance complexity
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations
- **Single Responsibility**: Each module has one reason to change
- **Open/Closed**: Architecture is open for extension, closed for modification
- **Interface Segregation**: Fine-grained, client-specific interfaces
- **Explicit Over Implicit**: Clear function signatures and behavior over "magic"
- **Resource Encapsulation**: Logical grouping of resources using ComponentResource pattern

## 2. Architectural Overview

### 2.1 Structural Organization

```
src/
├── core/
│   ├── __init__.py               # Clean public API exports
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── manager.py            # ConfigManager implementation
│   │   ├── loader.py             # Configuration loading utilities
│   │   ├── validator.py          # Schema validation
│   │   └── defaults.py           # Default configuration values
│   ├── deployment/               # Deployment orchestration
│   │   ├── __init__.py
│   │   ├── manager.py            # DeploymentManager implementation
│   │   ├── context.py            # Deployment context models
│   │   └── registry.py           # Module registry
│   ├── metadata/                 # Metadata management
│   │   ├── __init__.py
│   │   ├── manager.py            # MetadataManager implementation
│   │   ├── models.py             # Metadata models
│   │   └── transformations.py    # Resource transformations
│   ├── providers/                # Provider abstraction
│   │   ├── __init__.py
│   │   ├── registry.py           # Provider registry
│   │   ├── models.py             # Provider context models
│   │   └── factory.py            # Provider factory
│   ├── compliance/               # Compliance metadata management
│   │   ├── __init__.py
│   │   ├── models.py             # Compliance models
│   │   ├── validator.py          # Compliance validation
│   │   └── reporter.py           # Compliance reporting
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── git.py                # Git utilities
│   │   ├── pulumi.py             # Pulumi-specific utilities
│   │   └── serialization.py      # Data serialization helpers
│   ├── exceptions.py             # Exception hierarchy
│   ├── interfaces.py             # Core protocol definitions
│   └── types.py                  # Common type definitions
└── providers/                    # Provider implementations
    ├── aws/
    │   ├── resources/            # AWS resource implementations
    │   │   ├── __init__.py
    │   │   ├── s3/
    │   │   │   ├── __init__.py
    │   │   │   └── bucket.py     # S3 bucket implementation
    │   │   └── ...
    │   └── components/           # AWS component implementations
    │       ├── __init__.py
    │       ├── eks/
    │       │   ├── __init__.py
    │       │   └── cluster.py    # EKS cluster implementation
    │       └── ...
    └── ...
```

### 2.2 Key Subsystems

The architecture is organized into several key subsystems:

1. **Configuration Management**: Hierarchical configuration with validation
2. **Provider Abstraction**: Unified interface for cloud providers
3. **Resource Management**: Standardized resource creation and validation
4. **Component Composition**: Higher-level abstractions composed of resources
5. **Metadata Management**: Consistent tagging and annotation
6. **Compliance Metadata Framework**: Compliance metadata collection and reporting
7. **Deployment Orchestration**: Dependency-aware deployment sequencing

## 3. Component Resource Pattern Implementation

### 3.1 Overview of Component Resources

The ComponentResource pattern is a foundational element of our architecture. This pattern allows us to create higher-level abstractions that encapsulate multiple cloud resources into a single logical unit, providing better organization, reusability, and maintainability.

```python
import pulumi
from typing import Dict, Any, Optional

class BaseComponent(pulumi.ComponentResource):
    """Base class for all component resources."""

    def __init__(self,
                 resource_type: str,
                 name: str,
                 props: Dict[str, Any] = None,
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__(resource_type, name, props or {}, opts)
        self.resource_type = resource_type
        self.name = name

    def register_outputs(self, outputs: Dict[str, Any]):
        """Register component outputs to be tracked in Pulumi state."""
        super().register_outputs(outputs)
```

### 3.2 Benefits of Component Resources

By adopting the ComponentResource pattern, we gain several advantages:

1. **Resource Organization**: Resources are logically grouped, creating a clear hierarchy in the Pulumi resource graph
2. **State Management**: Component resources are tracked in Pulumi's state, making operations like `pulumi refresh` more effective
3. **Encapsulation**: Implementation details are hidden, exposing only necessary interfaces
4. **Reusability**: Components can be composed into higher-level abstractions
5. **Maintainability**: Changes to underlying resources can be made without impacting consumers

### 3.3 Component Resource Implementation

A typical component resource implementation follows this pattern:

```python
class SecureVpc(BaseComponent):
    """A secure VPC implementation with proper subnet isolation and security groups."""

    def __init__(self,
                 name: str,
                 config: Dict[str, Any],
                 opts: Optional[pulumi.ResourceOptions] = None):
        super().__init__("vpc:SecureVpc", name, {}, opts)

        # Create child resources with parent=self
        child_opts = pulumi.ResourceOptions(parent=self)

        # VPC creation
        self.vpc = aws.ec2.Vpc(
            f"{name}-vpc",
            cidr_block=config.get("cidr_block", "10.0.0.0/16"),
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={
                "Name": f"{name}-vpc",
                **config.get("tags", {})
            },
            opts=child_opts
        )

        # Create subnets
        self.public_subnets = []
        for i, az in enumerate(config.get("availability_zones", [])):
            subnet = aws.ec2.Subnet(
                f"{name}-public-{i}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i}.0/24",
                availability_zone=az,
                map_public_ip_on_launch=True,
                tags={
                    "Name": f"{name}-public-{i}",
                    "NetworkType": "public",
                    **config.get("tags", {})
                },
                opts=child_opts
            )
            self.public_subnets.append(subnet)

        # Register outputs that will be available to consumers
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "vpc_arn": self.vpc.arn,
            "public_subnet_ids": [subnet.id for subnet in self.public_subnets],
        })
```

### 3.4 Using Component Resources

Components are used in a straightforward manner, hiding the complexity of the underlying resources:

```python
# Configuration with our standardized structure
config = pulumi.Config()
aws_config = config.require_object("aws")

# Create the VPC component
vpc = SecureVpc(
    "main",
    config=aws_config.get("vpc", {}),
    opts=pulumi.ResourceOptions(protect=True)  # Protect from accidental deletion
)

# Use outputs from the component
pulumi.export("vpc_id", vpc.vpc_id)
pulumi.export("public_subnet_ids", vpc.public_subnet_ids)
```

## 4. Architecture Patterns and Design Considerations

### 4.1 Dependency Management Best Practices

Pulumi provides two primary mechanisms for managing resource dependencies, and it's critical to understand when to use each approach:

#### Parent/Child Relationships vs. depends_on

```python
# Example showing the difference between parent/child and depends_on

# Parent/Child relationship (preferred for logical grouping)
def create_database_server(name, opts=None):
    # Parent resource
    server = aws.rds.Instance(f"{name}-server",
                             engine="postgres",
                             # other properties...
                             opts=opts)

    # Child resources - automatically depend on the parent
    # These are logically "owned" by the server
    parameter_group = aws.rds.ParameterGroup(f"{name}-params",
                                           family="postgres13",
                                           # other properties...
                                           opts=pulumi.ResourceOptions(parent=server))

    subnet_group = aws.rds.SubnetGroup(f"{name}-subnets",
                                     subnet_ids=[...],
                                     # other properties...
                                     opts=pulumi.ResourceOptions(parent=server))

    return server, parameter_group, subnet_group

# depends_on relationship (for resources with a dependency but no ownership)
def create_application_with_dependencies(name, database_server):
    # Create an app that depends on the DB server but isn't "owned" by it
    app = aws.ecs.Service(f"{name}-app",
                         # other properties...
                         opts=pulumi.ResourceOptions(depends_on=[database_server]))

    return app
```

> **Important Note**: A single resource cannot be both a parent and a dependency (depends_on) of another resource. This creates circular dependencies in Pulumi and will cause deployment errors.

#### When to Use Parent/Child Relationships

- When there's a clear ownership relationship (parent logically owns children)
- When children should be deleted when the parent is deleted
- When grouping resources that belong together logically
- When building component resources that encapsulate a set of related resources

#### When to Use depends_on

- When resources have a deployment order dependency but no ownership relation
- When resources across different component resources need to coordinate
- When explicit ordering is needed but parent/child doesn't make sense

#### Best Practice Example

```python
class NetworkComponent(BaseComponent):
    def __init__(self, name, props, opts=None):
        super().__init__("infrastructure:network", name, props, opts)

        # Create VPC as a child of this component
        self.vpc = aws.ec2.Vpc(f"{name}-vpc",
                             cidr_block="10.0.0.0/16",
                             opts=pulumi.ResourceOptions(parent=self))

        # Create subnets as children of this component (siblings to VPC)
        self.public_subnet = aws.ec2.Subnet(f"{name}-public",
                                         vpc_id=self.vpc.id,  # Reference creates implicit dependency
                                         cidr_block="10.0.1.0/24",
                                         opts=pulumi.ResourceOptions(parent=self))

        # Register outputs
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "public_subnet_id": self.public_subnet.id
        })

# Usage with proper dependency management
network = NetworkComponent("prod-network", {})

# Security resources that depend on network but aren't parented by it
security_group = aws.ec2.SecurityGroup("app-sg",
                                     vpc_id=network.vpc_id,  # Reference creates implicit dependency
                                     # This is NOT parented by the NetworkComponent
                                     )

# Loadbalancer that depends on both network and security group
lb = aws.lb.LoadBalancer("app-lb",
                       subnets=[network.public_subnet_id],  # Implicit dependency through property reference
                       security_groups=[security_group.id],  # Implicit dependency through property reference
                       # depends_on not needed here due to implicit dependencies via property references
                       )

# Alternative explicit dependencies pattern when implicit isn't enough
lb_alternate = aws.lb.LoadBalancer("app-lb-alt",
                                 # properties...
                                 opts=pulumi.ResourceOptions(depends_on=[network, security_group]))
```

> **Caution**: Mixing parent/child relationships with depends_on for the same resources can lead to circular dependency errors. Always use one or the other, not both.

## 5. Key Subsystem Enhancements

### 5.1 Configuration Management

The configuration system has been significantly improved:

- **Hierarchical Configuration**: Default → Organization → Project → Stack → Override
- **Schema Validation**: JSON Schema validation for all configurations
- **Environment Variables**: Structured support for environment-based configuration
- **Configuration Discovery**: Automatic discovery of module configurations
- **Secret Management**: Enhanced integration with Pulumi's secret management

```python
class ConfigManager:
    def __init__(
        self,
        pulumi_config: Optional[pulumi.Config] = None,
        schema_validator: Optional[SchemaValidator] = None,
        config_loader: Optional[ConfigLoader] = None,
    ):
        self.pulumi_config = pulumi_config or pulumi.Config()
        self.schema_validator = schema_validator or SchemaValidator()
        self.config_loader = config_loader or ConfigLoader()

        # Load configuration in order of precedence
        self.configs = self._load_configuration_hierarchy()

    def _load_configuration_hierarchy(self) -> Dict[str, Any]:
        """Load configurations in order of precedence."""
        # Order: defaults → organization → project → stack → overrides
        configs = {}

        # Load default configurations
        defaults = self.config_loader.load_defaults()
        configs = deep_merge(configs, defaults)

        # Load organization configurations
        org_configs = self.config_loader.load_organization_configs()
        configs = deep_merge(configs, org_configs)

        # Continue with project, stack, and overrides...

        return configs
```

### 5.2 Component Discovery Catalog

A lightweight component discovery mechanism helps teams find and use available components:

```python
class ComponentCatalog:
    """
    Discovery catalog for available components with documentation and metadata.
    Unlike a registry, this doesn't create or manage resources - it just provides
    information about available components.
    """

    def __init__(self):
        self.components = {}

    def register_component(
        self,
        component_type: str,
        component_class: Type[pulumi.ComponentResource],
        description: str,
        examples: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Register component metadata for discovery."""
        if component_type in self.components:
            raise ValueError(f"Component type already registered: {component_type}")

        self.components[component_type] = {
            "class": component_class,
            "description": description,
            "examples": examples or [],
            "metadata": metadata or {},
        }

    def list_components(self, provider: str = None) -> List[str]:
        """List available components, optionally filtered by provider."""
        if provider:
            return [
                comp_type
                for comp_type, info in self.components.items()
                if comp_type.startswith(f"{provider}:")
            ]
        return list(self.components.keys())

    def get_component_info(self, component_type: str) -> Dict[str, Any]:
        """Get information about a specific component."""
        if component_type not in self.components:
            raise ValueError(f"Unknown component type: {component_type}")

        return self.components[component_type]
```

### 5.3 Module System

The module system has been redesigned around ComponentResource for cleaner dependency management:

```python
class ModuleRegistry:
    """
    Registry for all deployable modules.
    Manages module dependencies and deployment order.
    """

    def __init__(self):
        self.modules = {}
        self.dependency_graph = {}

    def register_module(
        self,
        module_name: str,
        module_class: Type[BaseComponent],
        dependencies: List[str] = None,
    ) -> None:
        """Register a module with its dependencies."""
        if module_name in self.modules:
            raise ValueError(f"Module already registered: {module_name}")

        # Ensure module_class is a BaseComponent
        if not issubclass(module_class, BaseComponent):
            raise TypeError(f"Module class must inherit from BaseComponent: {module_class.__name__}")

        self.modules[module_name] = module_class
        self.dependency_graph[module_name] = dependencies or []

    def get_deployment_order(self, selected_modules: List[str]) -> List[str]:
        """
        Determine the correct deployment order based on dependencies.
        """
        # Implementation of topological sort using the dependency graph
        # to determine correct deployment order
        visited = set()
        temp_visited = set()
        order = []

        def visit(module):
            if module in temp_visited:
                raise ValueError(f"Circular dependency detected involving {module}")
            if module in visited:
                return

            temp_visited.add(module)
            for dependency in self.dependency_graph.get(module, []):
                if dependency in selected_modules:
                    visit(dependency)

            temp_visited.remove(module)
            visited.add(module)
            order.append(module)

        for module in selected_modules:
            if module not in visited:
                visit(module)

        return order
```

### 5.4 Compliance Metadata Framework

The compliance system has been designed to collect and propagate compliance metadata for reporting and auditing:

```python
class ComplianceMetadataManager:
    """
    Manages compliance metadata, reporting, and audit trails.
    Does not implement enforcement, which is handled by external systems.
    """

    def __init__(
        self,
        metadata_manager: MetadataManagerProtocol,
        config_manager: ConfigManagerProtocol,
    ):
        self.metadata_manager = metadata_manager
        self.config_manager = config_manager
        self.frameworks = {}
        self.controls = {}

    def register_framework(
        self,
        framework_id: str,
        framework_class: type,
        config: Dict[str, Any] = None,
    ) -> None:
        """Register a compliance framework for metadata collection."""
        if framework_id in self.frameworks:
            raise ValueError(f"Framework already registered: {framework_id}")

        framework = framework_class(config or {})
        self.frameworks[framework_id] = framework

        # Register all controls from this framework
        for control_id, control in framework.get_controls().items():
            self.controls[f"{framework_id}:{control_id}"] = control

    def collect_component_metadata(
        self,
        component_type: str,
        args: Dict[str, Any],
        component=None,
    ) -> Dict[str, Any]:
        """
        Collect compliance metadata for a component and its resources.
        This data is used for reporting and auditing purposes.
        """
        metadata = {
            "component_type": component_type,
            "applicable_controls": [],
            "tags": {},
            "audit_trail": {
                "timestamp": datetime.now().isoformat(),
                "collected_by": "ComplianceMetadataManager",
            }
        }

        # Collect applicable control metadata
        for control_id, control in self.controls.items():
            if control.applies_to(component_type):
                control_meta = {
                    "control_id": control_id,
                    "description": control.description,
                    "framework": control_id.split(":")[0],
                }
                metadata["applicable_controls"].append(control_meta)

        # Add compliance tags for resource tracking
        for control in metadata["applicable_controls"]:
            tag_key = f"compliance:{control['framework']}:{control['control_id'].split(':')[1]}"
            metadata["tags"][tag_key] = "applicable"

        return metadata
```

> **Note**: This framework focuses on metadata collection and reporting, not enforcement. Compliance requirements are documented as metadata attached to resources for audit purposes.

## 6. Core APIs and Public Interfaces

### 6.1 Provider Interface

The Provider Interface has been completely redesigned for simplicity and flexibility:

```python
class Provider(Protocol):
    """Protocol defining the provider interface."""

    @property
    def name(self) -> str: ...

    @property
    def provider_type(self) -> str: ...

    def get_resource_factory(self, resource_type: str) -> Callable: ...

    def get_component_factory(self, component_type: str) -> Callable: ...

    def initialize(self, config: Dict[str, Any]) -> None: ...

    def validate_config(self, config: Dict[str, Any]) -> List[str]: ...
```

### 6.2 Resource Interfaces

We leverage Pulumi's native resource interfaces rather than creating parallel abstractions:

```python
# Using Pulumi's built-in resource interfaces

# Custom Resource (for provider-specific resources)
from pulumi import CustomResource

class SecureS3Bucket(CustomResource):
    """A secure S3 bucket with standardized security settings."""

    def __init__(self, name, args=None, opts=None):
        if args is None:
            args = {}

        # Apply security best practices
        args.setdefault("acl", "private")
        args.setdefault("versioning", {"enabled": True})

        # Apply server-side encryption by default
        if "server_side_encryption_configuration" not in args:
            args["server_side_encryption_configuration"] = {
                "rule": {
                    "apply_server_side_encryption_by_default": {
                        "sse_algorithm": "AES256"
                    }
                }
            }

        super().__init__("aws:s3/bucket:Bucket", name, args, opts)
```

### 6.3 Component Interfaces

For component resources, we extend Pulumi's native ComponentResource class:

```python
# Using Pulumi's built-in ComponentResource
from pulumi import ComponentResource, ResourceOptions

class NetworkStack(ComponentResource):
    """A network stack with VPC, subnets, and security groups."""

    def __init__(self, name, args=None, opts=None):
        super().__init__("infrastructure:network", name, {}, opts)

        if args is None:
            args = {}

        # Create child resources with this component as the parent
        child_opts = ResourceOptions(parent=self)

        # VPC and its components
        self.vpc = aws.ec2.Vpc(f"{name}-vpc",
                              cidr_block=args.get("cidr_block", "10.0.0.0/16"),
                              opts=child_opts)

        # Create subnets
        self.public_subnet = aws.ec2.Subnet(f"{name}-public",
                                          vpc_id=self.vpc.id,
                                          cidr_block="10.0.1.0/24",
                                          map_public_ip_on_launch=True,
                                          opts=child_opts)

        self.private_subnet = aws.ec2.Subnet(f"{name}-private",
                                           vpc_id=self.vpc.id,
                                           cidr_block="10.0.2.0/24",
                                           opts=child_opts)

        # Register outputs
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "public_subnet_id": self.public_subnet.id,
            "private_subnet_id": self.private_subnet.id
        })
```

> **Note**: By using Pulumi's native resource interfaces, we leverage all the built-in features of the platform, including automatic state tracking, dependency management, and secret handling. This approach adheres to Pulumi's architectural patterns rather than reinventing them.

## 7. Implementation Examples

### 7.1 AWS S3 Bucket Resource

The resource implementation enforces organizational standards:

```python
# src/providers/aws/resources/s3/bucket.py
from src.core.interfaces import ResourceInterface
import pulumi_aws as aws

class S3Bucket(ResourceInterface):
    """S3 Bucket resource implementation."""

    resource_type = "aws:s3:Bucket"
    provider_type = "aws"

    def __init__(self, registry):
        self.registry = registry

    def create(
        self,
        name: str,
        args: Dict[str, Any],
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> aws.s3.Bucket:
        """Create an S3 bucket with organizational standards."""
        # Enforce organizational standards
        args = self._enforce_standards(args)

        # Create the bucket
        return aws.s3.Bucket(name, **args, opts=opts)

    def _enforce_standards(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce organizational standards for S3 buckets."""
        # Ensure versioning is enabled unless explicitly disabled
        if "versioning" not in args:
            args["versioning"] = {"enabled": True}

        # Ensure encryption is enabled
        if "server_side_encryption_configuration" not in args:
            args["server_side_encryption_configuration"] = {
                "rule": {
                    "apply_server_side_encryption_by_default": {
                        "sse_algorithm": "AES256",
                    },
                },
            }

        # Ensure access logging is configured
        if "logging" not in args:
            # Get the logging bucket from configuration
            logging_bucket = self.registry.config_manager.get_aws_logging_bucket()
            if logging_bucket:
                args["logging"] = {
                    "target_bucket": logging_bucket,
                    "target_prefix": f"s3-logs/{name}/",
                }

        return args

    def validate_args(self, args: Dict[str, Any]) -> List[str]:
        """Validate arguments against schema and organizational policies."""
        errors = []

        # Check for public access
        if args.get("acl") in ["public-read", "public-read-write"]:
            errors.append("Public access ACLs are not allowed for S3 buckets")

        # Additional validation logic...

        return errors

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        """Get JSON Schema for this resource."""
        return {
            "type": "object",
            "properties": {
                "acl": {"type": "string"},
                "bucket": {"type": "string"},
                "versioning": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                    },
                },
                # Additional schema...
            },
            "required": ["acl"]
        }
```

### 7.2 Simplified Deployment Workflow

The deployment process has been streamlined:

```python
def deploy(stack_name: str, project_name: str) -> None:
    """Main entry point for deployment."""
    # Initialize core components
    config_manager = ConfigManager()
    metadata_manager = MetadataManager()
    provider_registry = ProviderRegistry()
    module_registry = ModuleRegistry()

    # Create deployment manager
    deployment_manager = DeploymentManager(
        config_manager=config_manager,
        metadata_manager=metadata_manager,
        provider_registry=provider_registry,
        module_registry=module_registry,
    )

    # Get enabled modules
    enabled_modules = config_manager.get_enabled_modules()

    # Get deployment order
    deployment_order = module_registry.get_deployment_order(enabled_modules)

    # Deploy modules in order
    for module_name in deployment_order:
        with DeploymentContext(deployment_manager, module_name) as ctx:
            # Get module config
            module_config = config_manager.get_module_config(module_name)

            # Get module class
            module_class = module_registry.get_module(module_name)

            # Create and deploy module
            module = module_class(
                metadata_manager=metadata_manager,
                provider_registry=provider_registry,
            )
            module.deploy(module_config)
```

## 8. Project Organization and Conventions

### 8.1 Project Structure

The refactored project structure follows established Python conventions:

```
project/
├── pyproject.toml              # Project metadata and build configuration
├── setup.py                    # Package setup script (if needed)
├── src/                        # Source code
│   ├── core/                   # Core module implementation
│   └── providers/              # Provider implementations
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
├── docs/                       # Documentation
│   ├── architecture/           # Architecture documentation
│   ├── api/                    # API documentation
│   └── examples/               # Example code
└── examples/                   # Example deployments
    ├── aws-infrastructure/     # AWS infrastructure example
    ├── multi-cloud/            # Multi-cloud example
    └── kubernetes/             # Kubernetes example
```

### 8.2 Documentation Conventions

All modules, classes, and functions include standardized docstrings:

```python
def apply_resource_transformations(
    resource_type: str,
    args: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply transformations to resource arguments based on type and metadata.

    Args:
        resource_type: The type of the resource to transform
        args: The resource arguments to transform
        metadata: Resource metadata to include in transformations

    Returns:
        Dict[str, Any]: The transformed resource arguments

    Raises:
        ValueError: If resource_type is unknown

    Example:
        ```python
        transformed_args = apply_resource_transformations(
            "aws:s3:Bucket",
            {"acl": "private"},
            {"environment": "production"}
        )
        ```
    """
    # Implementation...
```

## 9. Configuration Propagation System

### 9.1 Configuration Flow Architecture

The architecture implements a sophisticated configuration propagation system that enables seamless flow of configuration data from the core module to all provider modules while maintaining clear boundaries and autonomy.

```
┌────────────────────┐     ┌───────────────────┐     ┌───────────────────────┐
│                    │     │                   │     │                       │
│  Pulumi Stack      │────▶│  Core Config      │────▶│  Provider Modules     │
│  Configuration     │     │  Management       │     │  Configuration        │
│                    │     │                   │     │                       │
└────────────────────┘     └───────────────────┘     └───────────────────────┘
                                    │                           │
                                    │                           │
                                    ▼                           ▼
                           ┌───────────────────┐     ┌───────────────────────┐
                           │                   │     │                       │
                           │  Global Metadata  │     │  Resource/Component   │
                           │  Registry         │     │  Configuration        │
                           │                   │     │                       │
                           └───────────────────┘     └───────────────────────┘
```

The configuration system follows these key principles:

1. **Namespaced Configuration**: Each provider module has its own dedicated configuration namespace
2. **Configuration Sovereignty**: Provider teams maintain full control over their module's configuration schema
3. **Hierarchical Structure**: Supports deeply nested configuration objects with inheritance
4. **Dynamic Discovery**: Configuration is automatically discovered and loaded at runtime
5. **Schema Validation**: Each module defines and validates its own configuration schema

### 9.2 Configuration Loading Process

The configuration loading process follows a well-defined sequence:

```python
def load_and_propagate_configuration():
    # 1. Load the Pulumi stack configuration
    stack_config = pulumi.Config()

    # 2. Initialize the core configuration manager
    config_manager = ConfigManager(stack_config)

    # 3. Discover available provider modules
    provider_modules = discover_provider_modules()

    # 4. For each provider module, extract its namespaced configuration
    for module_name, module_class in provider_modules.items():
        # Extract the module's namespaced configuration
        module_config = config_manager.get_module_config(module_name)

        # Validate the module's configuration against its schema
        validation_errors = config_manager.validate_module_config(
            module_name, module_config
        )

        if validation_errors:
            raise ConfigurationError(
                f"Configuration errors in module {module_name}: {validation_errors}"
            )

        # Initialize the provider module with its configuration
        provider = module_class(module_config)

        # Register the provider
        provider_registry.register_provider(module_name, provider)
```

This process ensures that each provider module receives only its relevant configuration, properly validated against its schema.

### 9.3 Standardized Configuration Structure

The Pulumi stack configuration follows a standardized structure with consistent patterns across all provider modules:

```yaml
# Pulumi stack configuration (Pulumi.<stack-name>.yaml)
config:
  # Core configuration
  project:
    name: "example-project"
    environment: "dev" # "dev", "staging", "production"

  # AWS provider module configuration
  aws:
    enabled: true
    region: "us-west-2"
    profile: "example-profile"
    oidc_provider:  # OIDC moved to provider level
      enabled: true
      url: "https://oidc.eks.us-west-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE"
      client_id: "sts.amazonaws.com"
      thumbprint: "9e99a48a9960b14926bb7f3b02e22da2b0ab7280"
      audience: "sts.amazonaws.com"
    tags:
      Environment: "${project:environment}"
      Project: "${project:name}"
      ManagedBy: "pulumi"
    vpc:
      enabled: true
      cidr_block: "10.0.0.0/16"
      instance_tenancy: "default"
      enable_dns_support: true
      enable_dns_hostnames: true
    eks:
      enabled: true
      clusters:
        - name: "example-cluster"
          version: "1.26"
          endpoint_private_access: true
          endpoint_public_access: true
          public_access_cidrs: ["0.0.0.0/0"]
          node_groups:
            - name: "standard-workers"
              instance_type: "m5.large"
              min_size: 1
              max_size: 5
              desired_size: 3
```

The configuration follows these standardized patterns:

1. **Consistent Namespace Prefix**: All configuration uses a consistent prefix to avoid conflicts with other Pulumi packages
2. **Provider Namespacing**: Each provider has its own dedicated namespace (`aws:`, `azure:`, etc.)
3. **Enablement Flags**: All modules and major components have an `enabled` flag for selective activation
4. **Structured Credentials**: Credentials are consistently organized under a `credentials` object
5. **Hierarchical Organization**: Configuration is organized in a logical hierarchy (provider → component → resource)
6. **Consistent Naming Conventions**: Snake_case for keys, with descriptive names
7. **Declarative State Definition**: Configuration represents the desired state that Pulumi will reconcile automatically

### 9.3.1 Secure Secrets Management

The configuration system integrates directly with Pulumi's built-in secrets management to ensure sensitive information is handled securely:

```yaml
# Example of secure credential handling in configuration
aws:
  credentials:
    access_key_id:
      secure: "v1:encrypted-value"  # Encrypted by Pulumi
    secret_access_key:
      secure: "v1:encrypted-value"  # Encrypted by Pulumi
```

This approach provides several security benefits:

1. **Encryption at Rest**: Sensitive values are encrypted before being stored in the Pulumi state file
2. **Secure Display**: Encrypted values are masked in logs and CLI output
3. **Controlled Access**: Only authorized users with appropriate permissions can decrypt the values
4. **Backend Integration**: Leverages Pulumi's backend for secure key management (whether self-hosted or SaaS)

The configuration manager automatically detects values with the `secure` property and handles them appropriately:

```python
def process_secure_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Process secure values in configuration, integrating with Pulumi's secrets management."""
    result = {}

    for key, value in config.items():
        if isinstance(value, dict) and "secure" in value:
            # This is a secure value, use Pulumi's secret handling
            result[key] = pulumi.Output.secret(value["secure"])
        elif isinstance(value, dict):
            # Recursively process nested dictionaries
            result[key] = process_secure_values(value)
        else:
            # Regular value, no special handling needed
            result[key] = value

    return result
```

This ensures that sensitive information remains protected throughout the deployment lifecycle while still being accessible to authorized code and users.

The configuration manager parses this hierarchical structure into provider-specific configuration objects:

```python
# Resulting configuration object for the AWS provider module
aws_config = {
    "enabled": True,
    "region": "us-west-2",
    "profile": "example-profile",
    "oidc_provider": {
        "enabled": True,
        "url": "https://oidc.eks.us-west-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE",
        "client_id": "sts.amazonaws.com",
        "thumbprint": "9e99a48a9960b14926bb7f3b02e22da2b0ab7280",
        "audience": "sts.amazonaws.com"
    },
    "tags": {
        "Environment": "dev",
        "Project": "example-project",
        "ManagedBy": "pulumi"
    },
    "vpc": {
        "enabled": True,
        "cidr_block": "10.0.0.0/16",
        "instance_tenancy": "default",
        "enable_dns_support": True,
        "enable_dns_hostnames": True
    },
    "eks": {
        "enabled": True,
        "clusters": [
            {
                "name": "example-cluster",
                "version": "1.26",
                "endpoint_private_access": True,
                "endpoint_public_access": True,
                "public_access_cidrs": ["0.0.0.0/0"],
                "node_groups": [
                    {
                        "name": "standard-workers",
                        "instance_type": "m5.large",
                        "min_size": 1,
                        "max_size": 5,
                        "desired_size": 3
                    }
                ]
            }
        ]
    }
}
```

Similarly, other providers follow the same standardized schema pattern:

```python
class AzureProvider:
    @classmethod
    def config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether the Azure provider is enabled",
                    "default": False
                },
                "location": {
                    "type": "string",
                    "description": "Azure region to deploy resources to"
                },
                "credentials": {
                    "type": "object",
                    "description": "Azure credentials for authentication",
                    "properties": {
                        "entra_id": {
                            "type": "string",
                            "description": "Azure Entra ID"
                        },
                        "entra_secret": {
                            "type": "string",
                            "description": "Azure Entra Secret"
                        },
                        "subscription_id": {
                            "type": "string",
                            "description": "Azure Subscription ID"
                        },
                        "tenant_id": {
                            "type": "string",
                            "description": "Azure Tenant ID"
                        }
                    }
                },
                # Additional properties...
            },
            "required": ["enabled"]
        }
```

### 9.4 Provider Module Configuration Access

Each provider module and its resources/components access configuration through a consistent interface that respects the standardized configuration structure:

```python
class AwsProvider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)

        # Only proceed with initialization if the provider is enabled
        if not self.enabled:
            return

        # Extract common provider configuration
        self.region = config.get("region", "us-west-2")
        self.profile = config.get("profile")
        self.oidc_provider = config.get("oidc_provider", {})
        self.tags = config.get("tags", {})

        # Set up AWS provider configuration
        self.setup_provider()

        # Initialize AWS-specific resources and components
        self.initialize_resources()
        self.initialize_components()

    def setup_provider(self):
        """Configure the AWS provider with credentials and region."""
        provider_args = {
            "region": self.region
        }

        # Add profile if specified
        if self.profile:
            provider_args["profile"] = self.profile

        # Create the AWS provider
        self.provider = aws.Provider("aws-provider", **provider_args)

    def initialize_resources(self):
        # Only register resources if enabled
        if not self.enabled:
            return

        # Register S3 bucket resource
        s3_config = self.config.get("s3", {})
        if s3_config.get("enabled", False):
            self.register_resource(
                "s3:Bucket",
                S3BucketResource(s3_config, self.provider, self.tags)
            )

        # Register other resources...

    def initialize_components(self):
        # Only register components if enabled
        if not self.enabled:
            return

        # Register EKS cluster component if enabled
        eks_config = self.config.get("eks", {})
        if eks_config.get("enabled", False):
            # Process each cluster configuration
            for cluster_config in eks_config.get("clusters", []):
                self.register_component(
                    "eks:Cluster",
                    EksClusterComponent(cluster_config, self.provider, self.tags)
                )

        # Register other components...
```

### 9.5 Configuration Schema Validation

Each provider module defines a JSON Schema for its configuration, following the standardized structure:

```python
class AwsProvider:
    @classmethod
    def config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether the AWS provider is enabled",
                    "default": False
                },
                "region": {
                    "type": "string",
                    "description": "AWS region to deploy resources to"
                },
                "oidc_provider": {
                    "type": "object",
                    "description": "OIDC provider configuration",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether OIDC is enabled",
                            "default": False
                        },
                        "url": {
                            "type": "string",
                            "description": "OIDC provider URL"
                        },
                        "client_id": {
                            "type": "string",
                            "description": "OIDC client ID"
                        },
                        "thumbprint": {
                            "type": "string",
                            "description": "OIDC thumbprint"
                        },
                        "audience": {
                            "type": "string",
                            "description": "OIDC audience"
                        }
                    }
                },
                "tags": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    },
                    "description": "Tags to apply to all AWS resources"
                },
                "eks": {
                    "$ref": "#/definitions/eksConfig"
                },
                # Additional properties...
            },
            "required": ["enabled"],
            "definitions": {
                "eksConfig": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether EKS deployment is enabled",
                            "default": False
                        },
                        "clusters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "Name of the EKS cluster"
                                    },
                                    "version": {
                                        "type": "string",
                                        "description": "Kubernetes version for the EKS cluster"
                                    },
                                    "node_groups": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {
                                                    "type": "string",
                                                    "description": "Name of the node group"
                                                },
                                                "instance_type": {
                                                    "type": "string",
                                                    "description": "EC2 instance type for the node group"
                                                },
                                                "min_size": {
                                                    "type": "integer",
                                                    "description": "Minimum size of the node group"
                                                },
                                                "max_size": {
                                                    "type": "integer",
                                                    "description": "Maximum size of the node group"
                                                },
                                                "desired_size": {
                                                    "type": "integer",
                                                    "description": "Desired size of the node group"
                                                }
                                            },
                                            "required": ["name"]
                                        }
                                    }
                                },
                                "required": ["name"]
                            }
                        }
                    },
                    "required": ["enabled"]
                }
            }
        }
```

Similarly, other providers follow the same standardized schema pattern:

```python
class AzureProvider:
    @classmethod
    def config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether the Azure provider is enabled",
                    "default": False
                },
                "location": {
                    "type": "string",
                    "description": "Azure region to deploy resources to"
                },
                "credentials": {
                    "type": "object",
                    "description": "Azure credentials for authentication",
                    "properties": {
                        "entra_id": {
                            "type": "string",
                            "description": "Azure Entra ID"
                        },
                        "entra_secret": {
                            "type": "string",
                            "description": "Azure Entra Secret"
                        },
                        "subscription_id": {
                            "type": "string",
                            "description": "Azure Subscription ID"
                        },
                        "tenant_id": {
                            "type": "string",
                            "description": "Azure Tenant ID"
                        }
                    }
                },
                # Additional properties...
            },
            "required": ["enabled"]
        }
```

### 9.6 Configuration Inheritance and Overrides

The configuration system supports inheritance and overrides through a layered approach that aligns with our standardized configuration structure:

1. **Default Configuration**: Built-in defaults provided by the core module and provider modules
2. **Organization Configuration**: Organization-wide settings (e.g., common tags, compliance requirements)
3. **Project Configuration**: Project-specific settings (e.g., project name, region)
4. **Stack Configuration**: Environment-specific settings (dev, staging, production)
5. **Runtime Overrides**: Command-line or environment variable overrides for dynamic configuration

This layering allows for flexible configuration management while maintaining consistency across environments:

```python
def load_configuration_hierarchy() -> Dict[str, Any]:
    """
    Load configurations in order of precedence, with each layer overriding the previous.
    """
    # Start with empty configuration
    config = {}

    # 1. Load default configurations from provider modules
    defaults = load_default_configurations()
    config = merge_configurations(config, defaults)

    # 2. Load organization configurations
    org_config_path = os.environ.get("ORG_CONFIG", "./config/organization.yaml")
    if os.path.exists(org_config_path):
        org_config = load_yaml_config(org_config_path)
        config = merge_configurations(config, org_config)

    # 3. Load project configurations
    project_config_path = os.environ.get("PROJECT_CONFIG", "./config/project.yaml")
    if os.path.exists(project_config_path):
        project_config = load_yaml_config(project_config_path)
        config = merge_configurations(config, project_config)

    # 4. Load stack configurations from Pulumi stack
    stack_config = load_pulumi_stack_config()
    config = merge_configurations(config, stack_config)

    # 5. Apply any runtime overrides from environment variables
    env_overrides = load_environment_overrides()
    config = merge_configurations(config, env_overrides)

    return config

def merge_configurations(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two configurations, with override_config taking precedence.
    Handles complex nested structures including lists and dictionaries.
    Specifically designed to handle our standardized configuration structure.
    """
    result = copy.deepcopy(base_config)

    for key, override_value in override_config.items():
        # Handle provider namespaces (e.g., aws, azure)
        if key.startswith("provider:") and ":" in key:
            # Extract provider name from namespace
            _, provider = key.split(":", 1)

            # Handle nested provider configuration
            if provider not in result:
                result[provider] = {}

            # Merge provider configurations
            if isinstance(override_value, dict):
                result[provider] = merge_configurations(result.get(provider, {}), override_value)
            else:
                result[provider] = override_value

        # If both are dictionaries, recursively merge
        elif key in result and isinstance(result[key], dict) and isinstance(override_value, dict):
            result[key] = merge_configurations(result[key], override_value)

        # Handle lists of dictionaries with identifiable keys (e.g., clusters, node_groups)
        elif key in result and isinstance(result[key], list) and isinstance(override_value, list):
            # Attempt to merge lists of dictionaries by a common key if present
            if all(isinstance(item, dict) for item in result[key] + override_value):
                # Try common keys like 'name', 'id', etc.
                for id_key in ['name', 'id', 'key']:
                    if all(id_key in item for item in result[key] + override_value):
                        # Create a map of existing items by their ID
                        existing_items = {item[id_key]: item for item in result[key]}

                        # For each override item, either merge with existing or append
                        result[key] = []
                        for item in override_value:
                            if item[id_key] in existing_items:
                                # Merge with existing item
                                merged_item = merge_configurations(
                                    existing_items[item[id_key]], item
                                )
                                result[key].append(merged_item)
                                del existing_items[item[id_key]]
                            else:
                                # New item, just add it
                                result[key].append(item)

                        # Add remaining existing items
                        for item in existing_items.values():
                            result[key].append(item)

                        break
                else:
                    # No common ID key found, just replace the list
                    result[key] = override_value
            else:
                # Not a list of dictionaries, just replace
                result[key] = override_value

        # Handle special case for credentials (never merge, always override)
        elif key == "credentials":
            result[key] = override_value

        # For all other cases, override completely
        else:
            result[key] = override_value

    return result

def load_environment_overrides() -> Dict[str, Any]:
    """
    Load configuration overrides from environment variables.
    Environment variables should follow the pattern <PROVIDER>_<KEY>=<VALUE>
    For example: AWS_REGION=us-west-2
    """
    overrides = {}

    for env_key, env_value in os.environ.items():
        if env_key.startswith("AWS_") or env_key.startswith("AZURE_") or env_key.startswith("GCP_"):
            # Skip internal environment variables
            if env_key in ["ORG_CONFIG", "PROJECT_CONFIG"]:
                continue

            # Parse the environment variable key
            parts = env_key.split("_")

            if len(parts) >= 3:
                # Extract provider and key
                provider = parts[0].lower()
                key = "_".join(parts[1:]).lower()

                # Initialize provider in overrides if not exists
                if provider not in overrides:
                    overrides[provider] = {}

                # Set the override value
                current = overrides[provider]
                key_parts = key.split("_")

                # Handle nested keys
                for i, part in enumerate(key_parts):
                    if i == len(key_parts) - 1:
                        # Last part, set the value
                        current[part] = parse_env_value(env_value)
                    else:
                        # Intermediate part, ensure dict exists
                        if part not in current:
                            current[part] = {}
                        current = current[part]

    return overrides

def parse_env_value(value: str) -> Any:
    """Parse environment variable value to appropriate type."""
    # Try to parse as JSON first
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    # Handle boolean values
    if value.lower() in ["true", "yes", "1"]:
        return True
    if value.lower() in ["false", "no", "0"]:
        return False

    # Handle numeric values
    try:
        if "\n" in value or "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # Return as string for all other cases
    return value
```

This enhanced configuration system provides:

1. **Hierarchical Overrides**: Clear precedence for configuration values from different sources
2. **Environment Variable Support**: Dynamic configuration through environment variables
3. **Namespace Handling**: Proper handling of our standardized namespace prefixes
4. **Type Conversion**: Automatic conversion of configuration values to appropriate types
5. **Credential Protection**: Special handling for sensitive credential information

## 10. Conclusion

### 10.1 Benefits of the New Architecture

The refactored architecture delivers significant improvements:

- **Stronger Encapsulation**: Clear boundaries between subsystems
- **Improved Testability**: Dependency injection and pure functions
- **Enhanced Type Safety**: Comprehensive type annotations
- **Better Maintainability**: Smaller, focused modules with clear responsibilities
- **Consistent Standards**: Enforced organizational policies and compliance
- **Simplified Extension**: Easy addition of new providers and resources

### 10.2 Migration Strategy

Migration to the new architecture will follow these steps:

1. **Core Subsystems**: Implement the core subsystems first
3. **Resource Implementations**: Implement resources using the new interfaces
4. **Component Implementations**: Develop higher-level components
5. **Testing**: Comprehensive testing at each stage
6. **Documentation**: Update documentation to reflect the new architecture

### 10.3 Future Directions

Future enhancements to consider:

- **Cross-Stack References**: Improved handling of dependencies between stacks
- **Infrastructure Drift Detection**: Automated detection of manual changes

```
# Pulumi stack configuration (Pulumi.<stack-name>.yaml)
config:
  # Core configuration
  project:
    name: "example-project"
    environment: "dev" # "dev", "staging", "production"

  # AWS provider module configuration
  aws:
    enabled: true
    region: "us-west-2"
    profile: "example-profile"
    oidc_provider:  # OIDC moved to provider level
      enabled: true
      url: "https://oidc.eks.us-west-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE"
      client_id: "sts.amazonaws.com"
      thumbprint: "9e99a48a9960b14926bb7f3b02e22da2b0ab7280"
      audience: "sts.amazonaws.com"
    tags:
      Environment: "${project:environment}"
      Project: "${project:name}"
      ManagedBy: "pulumi"
    vpc:
      enabled: true
      cidr_block: "10.0.0.0/16"
      instance_tenancy: "default"
      enable_dns_support: true
      enable_dns_hostnames: true
    eks:
      enabled: true
      clusters:
        - name: "example-cluster"
          version: "1.26"
          endpoint_private_access: true
          endpoint_public_access: true
          public_access_cidrs: ["0.0.0.0/0"]
          node_groups:
            - name: "standard-workers"
              instance_type: "m5.large"
              min_size: 1
              max_size: 5
              desired_size: 3
