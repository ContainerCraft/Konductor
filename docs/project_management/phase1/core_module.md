# Phase1 MVP Core Module Implementation

# Core Module Implementation Design

## 1. Overview

The Core Module is the central foundation of our Infrastructure as Code (IaC) framework. It provides essential functionality that all provider modules depend on, and it must operate correctly even when all provider modules are disabled (`<provider_module_name>.enabled: false`). This document outlines the design and implementation details for the Core Module, focusing on its inputs, outputs, and standalone functionality.

## 2. Core Module Architecture

### 2.1 Overall Architecture

The Core Module follows a layered architecture with the following key components:

```
┌─────────────────────────────────────────────────────────────────┐
│                          Core Module                            │
│                                                                 │
│  ┌─────────────────┐    ┌────────────────┐    ┌──────────────┐  │
│  │   Configuration │    │    Metadata    │    │   Logging    │  │
│  │    Management   │    │   Management   │    │   System     │  │
│  └─────────────────┘    └────────────────┘    └──────────────┘  │
│                                                                 │
│  ┌─────────────────┐    ┌────────────────┐    ┌──────────────┐  │
│  │    Provider     │    │   Deployment   │    │     Git      │  │
│  │    Registry     │    │  Orchestration │    │   Integration│  │
│  └─────────────────┘    └────────────────┘    └──────────────┘  │
│                                                                 │
│  ┌─────────────────┐    ┌────────────────┐    ┌──────────────┐  │
│  │    Module       │    │     Dynamic    │    │    Stack     │  │
│  │   Discovery     │    │     Loading    │    │    Outputs   │  │
│  └─────────────────┘    └────────────────┘    └──────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Type System & Interfaces                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Subsystems

1. **Configuration Management**: Loads, validates, and propagates configuration from Pulumi stack YAML. Provider modules handle their own credential management with a fallback mechanism (config → environment variables → ambient credentials).

2. **Metadata Management**: Collects, validates, and propagates metadata such as tags, labels, and compliance annotations. Always collects Git metadata regardless of configuration.

3. **Logging System**: Provides standardized logging interfaces for all modules by wrapping Pulumi's native logging system. Supports multiple log levels (standard, verbose, debug) configurable via Pulumi stack config.

4. **Provider Registry**: Manages provider registration and discovery, including support for multiple named providers per module. Allows provider modules to register cross-provider dependencies (e.g., AWS EKS registering Kubernetes providers).

5. **Module Discovery**: Dynamically discovers provider modules without hardcoding, looking for modules in `src/providers/<provider_module_directory_name>`.

6. **Dynamic Loading**: Loads provider modules at runtime based on a standardized hook in each provider module's `__init__.py`.

7. **Deployment Orchestration**: Handles dependency management and deployment sequencing.

8. **Git Integration**: Always retrieves information from the local Git repository for metadata enrichment, returning fallback values if Git information is unavailable.

9. **Type System & Interfaces**: Defines core interfaces, types, and protocols that all modules implement.

## 3. Core Module Execution Flow

When running `pulumi up` with all provider modules disabled, the Core Module will execute the following sequence:

```
┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                  │     │                 │     │                 │
│Initialize Logging│────▶│Discover Provider│────▶│ Load & Validate │
│    System        │     │     Modules     │     │  Configuration  │
│                  │     │                 │     │                 │
└──────────────────┘     └─────────────────┘     └─────────────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌────────────────┐      ┌────────────────┐     ┌──────────────────┐
│                │      │                │     │                  │
│  Git Metadata  │─────▶│Process Metadata│────▶│Register Providers│
│   Collection   │      │                │     │                  │
│                │      │                │     │                  │
└────────────────┘      └────────────────┘     └──────────────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐     ┌────────────────┐     ┌──────────────────┐
│                 │     │                │     │                  │
│Initialize Module│────▶│ Generate Stack │────▶│  Output Program  │
│     Registry    │     │    Outputs     │     │      Status      │
│                 │     │                │     │                  │
└─────────────────┘     └────────────────┘     └──────────────────┘
```

### 3.1 Module Discovery

The Core Module dynamically discovers and loads provider modules without hardcoding specific providers:

1. **Discovery Phase**:
   - Scans the `src/providers/` directory for subdirectories
   - Each subdirectory represents a potential provider module
   - Loads each provider module's `__init__.py` to find standardized hooks

2. **Provider Registration Hooks**:
   - Each provider module must implement a standardized hook in its `__init__.py`:
     ```python
     # src/providers/aws/__init__.py example

     # Provider module metadata
     PROVIDER_NAME = "aws"  # Provider identifier
     PROVIDER_DISPLAY_NAME = "AWS"  # Human-readable name
     PROVIDER_VERSION = "1.0.0"  # Provider version

     # Primary entry point that Core Module will call
     def register_provider(provider_registry, config_manager, log_manager):
         """Register AWS provider with the core provider registry."""
         from .provider import AWSProvider

         # Register the provider
         provider_registry.register_provider(
             provider_name="aws",
             provider_class=AWSProvider
         )

         return True  # Success
     ```

3. **Testing Credentials**:
   - Each provider module is fully executable even when no resources or components are enabled
   - Provider modules test and log credential status (e.g., AWS STS get-caller-identity)
   - Provider modules handle their own credential loading and testing

## 4. Inputs and Outputs

### 4.1 Inputs

#### 4.1.1 Pulumi Stack Configuration (YAML)

The primary input is the Pulumi stack configuration (from `Pulumi.<stack-name>.yaml`), which follows this structure:

```yaml
config:
  # Core configuration
  project:
    name: "example-project"
    environment: "dev"  # "dev", "staging", "production"
    organization: "example-org"
    tags:
      # Global tags applied to all resources
      owner: "infrastructure-team"
      costCenter: "123456"

  # Logging configuration
  logging:
    level: "standard"  # "standard", "verbose", "debug" (default: "standard")

  # Metadata configuration
  metadata:
    compliance:
      frameworks:
        - name: "example-framework"
          version: "1.0"
          controls:
            - id: "control-1"
              description: "Example control description"

  # Provider configurations (all disabled for core-only mode)
  aws:
    enabled: false
    # ... other AWS configuration ...

  azure:
    enabled: false
    # ... other Azure configuration ...

  kubernetes:
    enabled: false
    # ... other Kubernetes configuration ...
```

#### 4.1.2 Provider-Specific Credential Loading

Each provider module handles its own credential loading with the following precedence:

1. **Pulumi Stack Configuration**: Credentials defined in the Pulumi stack configuration
2. **Environment Variables**: If not in config, check environment variables
3. **Ambient Credentials**: If not in environment, use default configured credentials

Examples of provider-specific credential loading:

**AWS Module** (handled by the AWS provider module, not the core module):
```python
def load_aws_credentials(config, region):
    """Load AWS credentials with fallback mechanism."""
    # 1. Try to get from config
    if "credentials" in config and "accessKeyId" in config["credentials"]:
        return {
            "access_key_id": config["credentials"]["accessKeyId"],
            "secret_access_key": config["credentials"]["secretAccessKey"],
            # Optional session token
            "session_token": config["credentials"].get("sessionToken"),
        }

    # 2. Try to get from environment variables
    if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        return {
            "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
            "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "session_token": os.environ.get("AWS_SESSION_TOKEN"),
        }

    # 3. Use ambient credentials (default profile or instance role)
    # Let Pulumi/AWS handle this automatically
    return None
```

#### 4.1.3 Git Repository Information

The Core Module always collects Git metadata from the local repository:

- Repository URL
- Current branch
- Latest commit hash
- Commit message
- Tag information (if the commit is tagged)

If Git metadata cannot be collected (e.g., not a Git repository), fallback values are used:

```python
def collect_git_metadata():
    """Collect Git metadata with fallbacks for missing data."""
    try:
        # Use GitPython or similar library to collect Git information
        import git
        repo = git.Repo(search_parent_directories=True)

        return {
            "repository": repo.remotes.origin.url,
            "branch": repo.active_branch.name,
            "commit": repo.head.commit.hexsha,
            "commit_message": repo.head.commit.message.strip(),
            "tag": next((tag.name for tag in repo.tags if tag.commit == repo.head.commit), None),
        }
    except Exception as e:
        # Return fallback values if Git information is unavailable
        return {
            "repository": "unknown",
            "branch": "unknown",
            "commit": "unknown",
            "commit_message": "unknown",
            "tag": None,
        }
```

### 4.2 Outputs

#### 4.2.1 Pulumi Stack Outputs

When all provider modules are disabled, the Core Module will still generate the following Pulumi stack outputs:

```
$ pulumi stack output state
{
  "metadata": {
    "git": {
      "repository": "https://github.com/example/example-project",
      "branch": "main",
      "commit": "1a2b3c4d5e6f7g8h9i0j",
      "tag": "v1.0.0"
    },
    "project": {
      "name": "example-project",
      "environment": "dev",
      "organization": "example-org"
    },
    "compliance": {
      "frameworks": [
        {
          "name": "example-framework",
          "version": "1.0",
          "controls": [
            {
              "id": "control-1",
              "description": "Example control description"
            }
          ]
        }
      ]
    }
  },
  "providers": {
    "aws": {
      "enabled": false
    },
    "azure": {
      "enabled": false
    },
    "kubernetes": {
      "enabled": false
    }
  }
}
```

For secure outputs like Kubernetes kubeconfig or other sensitive data, we use Pulumi's secret outputs:

```
$ pulumi stack output secrets
{
  "kubernetes": {
    "kubeconfig": "<encrypted-kubeconfig-data>"
  },
  "aws": {
    "temporaryCredentials": "<encrypted-credentials-data>"
  }
}
```

#### 4.2.2 Logs

The Core Module will produce detailed logs during its execution using a standardized logging framework that wraps Pulumi's native logging:

```
[core:INFO] Initializing core module (2025-03-18T12:10:15Z)
[core:INFO] Log level set to: standard
[core:INFO] Discovering provider modules in src/providers/
[core:INFO] Found provider modules: aws, azure, kubernetes
[core:INFO] Loading and validating configuration
[core:INFO] Collecting Git metadata
[core:INFO] Git repository: https://github.com/example/example-project
[core:INFO] Git branch: main
[core:INFO] Git commit: 1a2b3c4d5e6f7g8h9i0j
[core:INFO] Processing metadata
[core:INFO] Registering providers
[core:INFO] Provider status: AWS=disabled, Azure=disabled, Kubernetes=disabled
[core:INFO] All providers are disabled. Core module execution complete.
```

The logging system supports multiple log levels, controlled by the Pulumi stack configuration:

- **standard**: Default level, includes informational messages, warnings, and errors
- **verbose**: Includes additional details about operations
- **debug**: Includes low-level debugging information

If not specified in the configuration, the default log level is "standard".

## 5. Core Module Implementation

### 5.1 Core Module Directory Structure

```
src/
├── core/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_manager.py  # Configuration management
│   │   ├── schema.py          # Configuration schema validation
│   │   └── loaders.py         # Configuration loaders
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── log_manager.py     # Logging infrastructure
│   │   └── formatters.py      # Log formatters
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── metadata_manager.py # Metadata management
│   │   ├── git.py             # Git metadata collection
│   │   └── compliance.py      # Compliance metadata
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── provider_registry.py # Provider registration
│   │   └── provider_factory.py  # Provider instantiation
│   ├── types/
│   │   ├── __init__.py
│   │   └── common.py          # Common type definitions
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── provider.py        # Provider interface
│   │   ├── resource.py        # Resource interface
│   │   └── component.py       # Component interface
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── exceptions.py      # Exception hierarchy
│   └── utils/
│       ├── __init__.py
│       ├── git.py             # Git utilities
│       └── pulumi.py          # Pulumi utilities
└── main.py                    # Main entry point
```

### 5.2 Key Classes and Interfaces

#### 5.2.1 Minimal Main Entry Point

```python
# src/__main__.py

"""Main entry point for the Pulumi program."""

# Minimal entry point that delegates to the Core Module
from core.core_module import CoreModule

def main():
    """Initialize and run the Core Module."""
    core_module = CoreModule()
    core_module.run()

# Entry point
if __name__ == "__main__":
    main()
```

#### 5.2.2 Core Module Implementation

```python
# src/core/core_module.py

"""Core Module implementation."""

import pulumi
import os
import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Type

from .logging import LogManager
from .config import ConfigManager
from .metadata import MetadataManager
from .providers import ProviderRegistry, ProviderDiscovery


class CoreModule:
    """Main Core Module implementation."""

    def __init__(self):
        """Initialize the Core Module."""
        # Initialize logging first
        self.log_manager = LogManager()
        self.logger = self.log_manager.get_logger("core")
        self.logger.info("Initializing core module")

        # Initialize configuration
        self.config_manager = ConfigManager(self.log_manager)

        # Initialize metadata management
        self.metadata_manager = MetadataManager(self.config_manager, self.log_manager)

        # Initialize provider registry
        self.provider_registry = ProviderRegistry(self.config_manager, self.log_manager)

        # Initialize provider discovery
        self.provider_discovery = ProviderDiscovery(self.log_manager)

    def run(self):
        """Execute the Core Module."""
        try:
            # Apply log level from configuration
            self._configure_logging()

            # Discover and load provider modules
            self._discover_provider_modules()

            # Load and validate configuration
            self.logger.info("Loading and validating configuration")
            self.config_manager.load()
            validation_errors = self.config_manager.validate()
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(f"Configuration error: {error}")
                raise Exception("Configuration validation failed")

            # Collect Git metadata
            self.logger.info("Collecting Git metadata")
            git_metadata = self.metadata_manager.collect_git_metadata()

            # Process all metadata
            self.logger.info("Processing metadata")
            metadata = self.metadata_manager.collect_metadata()

            # Register provider modules
            self.logger.info("Registering providers")
            self._register_provider_modules()

            # Initialize module registry
            self.logger.info("Initializing module registry")

            # Generate stack outputs
            self._generate_stack_outputs(metadata)

            # Log completion status
            self.logger.info("Core module execution complete")

        except Exception as e:
            self.logger.error(f"Core module execution failed: {str(e)}")
            raise e

    def _configure_logging(self):
        """Configure logging based on configuration."""
        config = self.config_manager.get_config().get("logging", {})
        log_level = config.get("level", "standard")
        self.log_manager.set_log_level(log_level)
        self.logger.info(f"Log level set to: {log_level}")

    def _discover_provider_modules(self):
        """Discover available provider modules."""
        self.logger.info("Discovering provider modules")
        provider_modules = self.provider_discovery.discover_provider_modules()

        if provider_modules:
            self.logger.info(f"Found provider modules: {', '.join(provider_modules)}")
        else:
            self.logger.warning("No provider modules found")

    def _register_provider_modules(self):
        """Register discovered provider modules with the provider registry."""
        for provider_module_name, provider_module in self.provider_discovery.get_provider_modules().items():
            self.logger.info(f"Registering provider module: {provider_module_name}")
            try:
                # Call the provider's register_provider hook
                if hasattr(provider_module, "register_provider"):
                    provider_module.register_provider(
                        self.provider_registry,
                        self.config_manager,
                        self.log_manager
                    )
                else:
                    self.logger.warning(f"Provider module {provider_module_name} does not implement register_provider hook")
            except Exception as e:
                self.logger.error(f"Failed to register provider module {provider_module_name}: {str(e)}")

    def _generate_stack_outputs(self, metadata: Dict[str, Any]):
        """Generate Pulumi stack outputs."""
        self.logger.info("Generating stack outputs")

        # Export main state output
        state_output = {
            "metadata": metadata,
            "providers": {}
        }

        # Add provider status to state output
        for provider_name in self.provider_discovery.get_provider_modules().keys():
            enabled = self.config_manager.is_provider_enabled(provider_name)
            state_output["providers"][provider_name] = {"enabled": enabled}
            self.logger.info(f"Provider {provider_name} is {'enabled' if enabled else 'disabled'}")

        # Export state output
        pulumi.export("state", state_output)

        # Export secrets output if any secrets are registered
        secrets = {}
        # Collect secrets from provider modules (would be implemented in full version)
        if secrets:
            pulumi.export("secrets", pulumi.Output.secret(secrets))
```

#### 5.2.3 Dynamic Provider Discovery

```python
# src/core/providers/provider_discovery.py

"""Provider module discovery and loading."""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, List


class ProviderDiscovery:
    """Discovers and loads provider modules dynamically."""

    def __init__(self, log_manager):
        """Initialize provider discovery."""
        self.log_manager = log_manager
        self.logger = log_manager.get_logger("provider_discovery")
        self.provider_modules = {}
        self.providers_dir = Path("src/providers")

    def discover_provider_modules(self) -> List[str]:
        """Discover available provider modules."""
        if not self.providers_dir.exists() or not self.providers_dir.is_dir():
            self.logger.warning(f"Providers directory not found: {self.providers_dir}")
            return []

        # Find all subdirectories in the providers directory
        provider_dirs = [d for d in self.providers_dir.iterdir() if d.is_dir() and not d.name.startswith('_')]

        for provider_dir in provider_dirs:
            provider_name = provider_dir.name
            self.logger.debug(f"Found potential provider module: {provider_name}")

            # Check for __init__.py to confirm it's a Python module
            init_file = provider_dir / "__init__.py"
            if not init_file.exists():
                self.logger.warning(f"Provider directory {provider_name} missing __init__.py, skipping")
                continue

            # Load the provider module
            try:
                # Construct the module name
                module_name = f"providers.{provider_name}"

                # Add the parent directory to sys.path if needed
                parent_dir = str(self.providers_dir.parent)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)

                # Import the module
                provider_module = importlib.import_module(module_name)

                # Verify it has the required attributes
                if not hasattr(provider_module, "PROVIDER_NAME"):
                    self.logger.warning(f"Provider module {provider_name} missing PROVIDER_NAME attribute")
                    continue

                # Store the module for later use
                self.provider_modules[provider_name] = provider_module
                self.logger.info(f"Successfully loaded provider module: {provider_name}")

            except Exception as e:
                self.logger.error(f"Failed to load provider module {provider_name}: {str(e)}")

        return list(self.provider_modules.keys())

    def get_provider_modules(self) -> Dict[str, Any]:
        """Get all discovered provider modules."""
        return self.provider_modules

    def get_provider_module(self, provider_name: str) -> Optional[Any]:
        """Get a specific provider module."""
        return self.provider_modules.get(provider_name)
```

#### 5.2.4 Enhanced Logging System

```python
# src/core/logging/log_manager.py

"""Standardized logging system that wraps Pulumi's native logging."""

import pulumi
import logging
import sys
from typing import Dict, Any, Optional


class LogManager:
    """Manages logging for all modules, wrapping Pulumi's native logging."""

    # Log levels mapping
    LOG_LEVELS = {
        "standard": 0,  # Default level
        "verbose": 1,  # More detailed information
        "debug": 2     # Low-level debugging
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the logging system."""
        self.config = config or {}
        self.loggers = {}
        self.current_level = "standard"  # Default level
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure the logging system."""
        # Set up console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "[%(name)s:%(levelname)s] %(message)s"
        ))

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance with standardized configuration."""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger

            # Wrap log methods to also use Pulumi logging
            original_info = logger.info
            original_warning = logger.warning
            original_error = logger.error
            original_debug = logger.debug

            # Override methods to also log to Pulumi
            def info_wrapper(msg, *args, **kwargs):
                original_info(msg, *args, **kwargs)
                pulumi.log.info(msg, resource=None)

            def warning_wrapper(msg, *args, **kwargs):
                original_warning(msg, *args, **kwargs)
                pulumi.log.warn(msg, resource=None)

            def error_wrapper(msg, *args, **kwargs):
                original_error(msg, *args, **kwargs)
                pulumi.log.error(msg, resource=None)

            def debug_wrapper(msg, *args, **kwargs):
                original_debug(msg, *args, **kwargs)
                if self.get_log_level_value() >= self.LOG_LEVELS["debug"]:
                    pulumi.log.debug(msg, resource=None)

            # Replace the methods
            logger.info = info_wrapper
            logger.warning = warning_wrapper
            logger.error = error_wrapper
            logger.debug = debug_wrapper

        return self.loggers[name]

    def set_log_level(self, level: str) -> None:
        """Set the log level."""
        if level not in self.LOG_LEVELS:
            level = "standard"  # Default to standard if invalid level

        self.current_level = level

        # Set Python logging level
        root_logger = logging.getLogger()
        if level == "debug":
            root_logger.setLevel(logging.DEBUG)
        elif level == "verbose":
            root_logger.setLevel(logging.INFO)
        else:  # standard
            root_logger.setLevel(logging.INFO)

    def get_log_level_value(self) -> int:
        """Get the numeric value of the current log level."""
        return self.LOG_LEVELS.get(self.current_level, 0)
```

### 5.2.5 Provider Registry System

```python
# src/core/providers/provider_registry.py

"""Provider registration and management."""

from typing import Dict, Any, List, Optional, Type, Callable
from abc import ABC, abstractmethod


# Provider interface
class ProviderProtocol(ABC):
    """Protocol defining the provider interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        pass

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Get the provider type."""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the provider is enabled."""
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration."""
        pass


class ProviderRegistry:
    """Registry for all providers."""

    def __init__(self, config_manager, log_manager):
        """Initialize the provider registry."""
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.logger = log_manager.get_logger("provider_registry")
        # Structure: {provider_type: {provider_name: provider_instance}}
        self.providers: Dict[str, Dict[str, Any]] = {}
        # Structure: {provider_type: factory_function}
        self.provider_factories: Dict[str, Callable] = {}

    def register_provider_factory(self, provider_type: str, factory_function: Callable) -> None:
        """Register a provider factory function.

        Args:
            provider_type: Type of the provider (e.g., 'aws', 'azure', 'kubernetes')
            factory_function: Function that creates provider instances
        """
        self.logger.info(f"Registering provider factory for type: {provider_type}")
        self.provider_factories[provider_type] = factory_function

        # Initialize the provider type registry if needed
        if provider_type not in self.providers:
            self.providers[provider_type] = {}

    def create_provider(self, provider_type: str, provider_name: str, **kwargs) -> Optional[Any]:
        """Create a provider instance using the registered factory.

        Args:
            provider_type: Type of the provider
            provider_name: Name of the provider instance
            **kwargs: Additional parameters for the factory function

        Returns:
            The created provider instance or None if factory not found
        """
        if provider_type not in self.provider_factories:
            self.logger.warning(f"No provider factory registered for type: {provider_type}")
            return None

        try:
            self.logger.info(f"Creating provider: {provider_name} of type: {provider_type}")
            provider = self.provider_factories[provider_type](provider_name, **kwargs)

            # Store the provider in the registry
            self.providers[provider_type][provider_name] = provider
            return provider
        except Exception as e:
            self.logger.error(f"Failed to create provider {provider_name} of type {provider_type}: {str(e)}")
            return None

    def get_provider(self, provider_type: str, provider_name: str) -> Optional[Any]:
        """Get a provider instance from the registry.

        Args:
            provider_type: Type of the provider
            provider_name: Name of the provider instance

        Returns:
            The provider instance or None if not found
        """
        if provider_type not in self.providers:
            return None
        return self.providers[provider_type].get(provider_name)

    def get_enabled_providers(self) -> List[Any]:
        """Get all enabled providers.

        Returns:
            List of enabled provider instances
        """
        enabled_providers = []
        for provider_type, providers in self.providers.items():
            for provider in providers.values():
                if provider.is_enabled():
                    enabled_providers.append(provider)
        return enabled_providers

    def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered providers.

        Returns:
            Dictionary of all registered providers
        """
        return self.providers

    def has_provider_type(self, provider_type: str) -> bool:
        """Check if a provider type is registered.

        Args:
            provider_type: Type of the provider

        Returns:
            True if the provider type is registered, False otherwise
        """
        return provider_type in self.providers
```

#### 5.2.6 Provider Module Registration Hook Example

```python
# src/providers/aws/__init__.py

"""AWS Provider Module for the IaC framework."""

PROVIDER_TYPE = "aws"
PROVIDER_NAME = "aws"  # Default provider name


def register_provider(provider_registry, config_manager, log_manager):
    """Register the AWS provider with the provider registry.

    This is the standardized hook called by the Core Module during provider registration.

    Args:
        provider_registry: The provider registry instance
        config_manager: The configuration manager instance
        log_manager: The logging manager instance
    """
    from .provider import create_aws_provider

    logger = log_manager.get_logger("aws_provider")
    logger.info(f"Registering AWS provider factory")

    # Register the AWS provider factory
    provider_registry.register_provider_factory(PROVIDER_TYPE, create_aws_provider)

    # Get AWS provider configurations
    aws_config = config_manager.get_provider_config(PROVIDER_TYPE)

    # Create default AWS provider if enabled
    if config_manager.is_provider_enabled(PROVIDER_TYPE):
        # Create the default AWS provider
        provider = provider_registry.create_provider(
            PROVIDER_TYPE,
            PROVIDER_NAME,
            config=aws_config.get("default", {}),
            config_manager=config_manager,
            log_manager=log_manager
        )

        if provider:
            logger.info(f"Created default AWS provider: {PROVIDER_NAME}")

        # Create any additional named AWS providers
        named_providers = aws_config.get("providers", {})
        for name, provider_config in named_providers.items():
            if name == "default":
                continue  # Skip default, already created

            provider = provider_registry.create_provider(
                PROVIDER_TYPE,
                name,
                config=provider_config,
                config_manager=config_manager,
                log_manager=log_manager
            )

            if provider:
                logger.info(f"Created named AWS provider: {name}")
    else:
        logger.info("AWS provider is disabled, skipping provider creation")
```

### 5.3 Main Entry Point

```python
import pulumi
from typing import Dict, Any

# Import core module components
from core.config import ConfigManager
from core.metadata import MetadataManager
from core.logging import LogManager
from core.providers import ProviderRegistry


def main():
    """Main entry point for the Pulumi program."""
    # Initialize logging
    log_manager = LogManager()
    logger = log_manager.get_logger("main")
    logger.info("Initializing core module")

    # Initialize configuration management
    config_manager = ConfigManager()
    logger.info("Loaded configuration")

    # Validate configuration
    validation_errors = config_manager.validate_config()
    if validation_errors:
        for error in validation_errors:
            logger.error(f"Configuration error: {error}")
        raise Exception("Configuration validation failed")

    # Initialize metadata management
    metadata_manager = MetadataManager(config_manager)
    metadata = metadata_manager.collect_metadata()
    logger.info("Collected metadata")

    # Initialize provider registry
    provider_registry = ProviderRegistry(config_manager)
    logger.info("Initialized provider registry")

    # Check which providers are enabled
    aws_enabled = config_manager.is_provider_enabled("aws")
    azure_enabled = config_manager.is_provider_enabled("azure")
    kubernetes_enabled = config_manager.is_provider_enabled("kubernetes")

    logger.info(f"Provider status: AWS={'enabled' if aws_enabled else 'disabled'}, "
                f"Azure={'enabled' if azure_enabled else 'disabled'}, "
                f"Kubernetes={'enabled' if kubernetes_enabled else 'disabled'}")

    # Log metadata
    logger.info(f"Project: {metadata.get('project', {}).get('name', 'unknown')}")
    logger.info(f"Environment: {metadata.get('project', {}).get('environment', 'unknown')}")

    # Get Git metadata
    git_metadata = metadata.get("git", {})
    if git_metadata:
        logger.info(f"Git repository: {git_metadata.get('repository', 'unknown')}")
        logger.info(f"Git branch: {git_metadata.get('branch', 'unknown')}")
        logger.info(f"Git commit: {git_metadata.get('commit', 'unknown')}")
        if "tag" in git_metadata:
            logger.info(f"Git tag: {git_metadata.get('tag')}")

    # Register Pulumi stack outputs
    pulumi.export("metadata", metadata)
    pulumi.export("providers", {
        "aws": {"enabled": aws_enabled},
        "azure": {"enabled": azure_enabled},
        "kubernetes": {"enabled": kubernetes_enabled}
    })

    # Only proceed with provider initialization if they are enabled
    if not any([aws_enabled, azure_enabled, kubernetes_enabled]):
        logger.info("All providers are disabled. Core module execution complete.")
        return

    # Initialize enabled providers (not part of this design document)
    # ...


# Entry point
if __name__ == "__main__":
    main()
```

## 6. Testing Core Module Functionality

### 6.1 Unit Testing

Key unit tests for the Core Module will include:

1. **Dynamic Module Discovery Tests**:
   - Test module discovery mechanics
   - Test module loading with valid and invalid modules
   - Test handling of missing required hooks

2. **Configuration Management Tests**:
   - Test loading configuration from Pulumi stack
   - Test configuration validation
   - Test provider enablement detection

3. **Metadata Management Tests**:
   - Test metadata collection
   - Test Git metadata extraction with and without Git repository
   - Test compliance metadata processing
   - Test tag generation for resources

4. **Logging System Tests**:
   - Test logger creation and Pulumi logging integration
   - Test log level configuration (standard, verbose, debug)
   - Test log formatting

5. **Provider Registry Tests**:
   - Test provider registration
   - Test provider retrieval
   - Test cross-provider registration (e.g., AWS EKS registering Kubernetes providers)
   - Test enabled provider filtering

### 6.2 Integration Testing

Integration tests will verify the Core Module's functionality in an end-to-end scenario:

1. **Core-Only Mode Test**: Run Pulumi with all providers disabled and verify:
   - Configuration is loaded and validated
   - Metadata is collected and exported
   - Logs contain expected information
   - Stack outputs contain correct metadata

2. **Provider Module Loading Test**: Test the dynamic loading of provider modules:
   - Test discovery of standard provider modules
   - Test handling of invalid provider modules
   - Test loading provider modules with all resources disabled

3. **Cross-Provider Integration Test**: Test scenarios where provider modules register providers with other modules:
   - Test AWS EKS registering Kubernetes provider
   - Test Azure AKS registering Kubernetes provider
   - Test proper separation of credentials and configuration between providers

## 7. Next Steps

After implementing the Core Module, subsequent steps will include:

1. **Provider Module Implementation**: Implement AWS, Azure, and Kubernetes provider modules with proper hooks for registration

2. **Provider-Specific Credentials Management**: Implement credential loading and validation in each provider module

3. **Cross-Provider Integration**: Implement cross-provider integration patterns (e.g., AWS EKS → Kubernetes)

4. **Resource and Component Implementation**: Implement core resources and components for each provider

5. **End-to-End Testing**: Test the entire framework with real infrastructure

## 8. Conclusion

The Core Module design provides a solid foundation for our IaC framework, offering essential functionality that works even when all provider modules are disabled. Key enhancements in this design include:

1. **Dynamic Provider Loading**: Provider modules are discovered and loaded dynamically from `src/providers/<provider_module_directory_name>` without hardcoding in the core module or main entry point.

2. **Standardized Provider Registration Hooks**: Each provider module implements a standardized hook in its `__init__.py` to register with the core module.

3. **Provider-Specific Credential Management**: Each provider handles its own credential loading with a consistent fallback mechanism (config → environment variables → ambient credentials).

4. **Always-Collected Git Metadata**: Git metadata is always collected, with fallback values when Git information is unavailable.

5. **Minimal Main Entry Point**: The main entry point (`__main__.py`) contains minimal code, delegating all logic to the Core Module.

6. **Named Stack Outputs**: Stack outputs are named meaningfully with separate outputs for state and secrets.

7. **Standardized Pulumi-Wrapped Logging**: The logging system wraps Pulumi's native logging for consistent formatting and multiple log levels.

With this design, the Core Module will successfully execute in standalone mode, providing valuable metadata outputs and comprehensive logging while validating all configuration before any resources are provisioned. The modular architecture with dynamic provider loading ensures clean separation of concerns and allows for easy extension with new provider modules in the future.

## 9. Appendix: Sample Configuration

### 9.1 Pulumi Stack Configuration Example

Below is a sample Pulumi stack configuration file (`Pulumi.<stack-name>.yaml`) that demonstrates the expected format for configuring the core module and provider modules:

```yaml
config:
  # Core Module Configuration
  core:
    # Project metadata
    project:
      name: "example-iac-project"
      environment: "dev"
      owner: "platform-team"
      costCenter: "12345"

    # Logging configuration
    logging:
      level: "verbose"  # Options: standard, verbose, debug

  # AWS Provider Configuration
  aws:
    enabled: true
    region: "us-west-2"  # Default region
    tags:  # Default tags for all AWS resources
      Environment: "dev"
      ManagedBy: "pulumi"

    # Multiple named providers
    providers:
      default:  # Default provider (can be omitted, uses values above)
        region: "us-west-2"
      east:
        region: "us-east-1"
        tags:
          Region: "east"

    # Service-specific configurations
    services:
      s3:
        enabled: true
        defaultBucketConfig:
          versioning: true
          encryption: true

      ec2:
        enabled: true
        defaultInstanceType: "t3.micro"

  # Azure Provider Configuration
  azure:
    enabled: false  # Provider is disabled
    location: "westus2"  # Default region
    tags:  # Default tags for all Azure resources
      environment: "dev"
      managedBy: "pulumi"

  # Kubernetes Provider Configuration
  kubernetes:
    enabled: true
    # Default provider configuration
    default:
      namespace: "default"
      versionControlEnabled: true
      versionControl:
        repo: "https://github.com/org/k8s-configs"
        path: "env/dev"
        branch: "main"

    # Multiple named providers (e.g., for different clusters)
    providers:
      dev-cluster:
        namespace: "dev"
      prod-cluster:
        enabled: false  # This specific provider is disabled
        namespace: "prod"
```

### 9.2 Provider Module Directory Structure Example

Example directory structure for a provider module (AWS):

```
src/
├── providers/
    ├── aws/
    │   ├── __init__.py           # Provider registration hook
    │   ├── provider.py           # Provider implementation
    │   ├── config/
    │   │   ├── __init__.py
    │   │   ├── schema.py         # AWS configuration schema
    │   │   └── validators.py     # AWS-specific validators
    │   ├── resources/
    │   │   ├── __init__.py
    │   │   ├── s3.py             # S3 bucket resources
    │   │   └── ec2.py            # EC2 instance resources
    │   ├── components/
    │   │   ├── __init__.py
    │   │   ├── web_app.py        # Web application component
    │   │   └── database.py       # Database component
    │   ├── utils/
    │   │   ├── __init__.py
    │   │   └── aws_helpers.py    # AWS-specific helper functions
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_provider.py  # Provider tests
    │       └── test_resources.py # Resource tests
    └── azure/
        ├── ...
```

### 9.3 Provider Module Implementation Example

Below is an example implementation of a provider module's key files:

#### 9.3.1 Provider Registration Hook (`__init__.py`)

```python
# src/providers/aws/__init__.py

"""AWS Provider Module for the IaC framework."""

PROVIDER_TYPE = "aws"
PROVIDER_NAME = "aws"  # Default provider name
PROVIDER_DISPLAY_NAME = "AWS"  # Human-readable name


def register_provider(provider_registry, config_manager, log_manager):
    """Register the AWS provider with the provider registry.

    This is the standardized hook called by the Core Module during provider registration.

    Args:
        provider_registry: The provider registry instance
        config_manager: The configuration manager instance
        log_manager: The logging manager instance
    """
    from .provider import create_aws_provider

    logger = log_manager.get_logger("aws_provider")
    logger.info(f"Registering AWS provider factory")

    # Register the AWS provider factory
    provider_registry.register_provider_factory(PROVIDER_TYPE, create_aws_provider)

    # Get AWS provider configurations
    aws_config = config_manager.get_provider_config(PROVIDER_TYPE)

    # Create default AWS provider if enabled
    if config_manager.is_provider_enabled(PROVIDER_TYPE):
        # Create the default AWS provider
        provider = provider_registry.create_provider(
            PROVIDER_TYPE,
            PROVIDER_NAME,
            config=aws_config.get("default", {}),
            config_manager=config_manager,
            log_manager=log_manager
        )

        if provider:
            logger.info(f"Created default AWS provider: {PROVIDER_NAME}")

        # Create any additional named AWS providers
        named_providers = aws_config.get("providers", {})
        for name, provider_config in named_providers.items():
            if name == "default":
                continue  # Skip default, already created

            provider = provider_registry.create_provider(
                PROVIDER_TYPE,
                name,
                config=provider_config,
                config_manager=config_manager,
                log_manager=log_manager
            )

            if provider:
                logger.info(f"Created named AWS provider: {name}")
    else:
        logger.info("AWS provider is disabled, skipping provider creation")
```

#### 9.3.2 Provider Implementation (`provider.py`)

```python
# src/providers/aws/provider.py

"""AWS Provider implementation."""

import pulumi
import pulumi_aws as aws
import os
from typing import Dict, Any, Optional

from core.interfaces.provider import ProviderProtocol


class AwsProvider(ProviderProtocol):
    """AWS Provider implementation."""

    def __init__(self, provider_name: str, config: Dict[str, Any], config_manager, log_manager):
        """Initialize AWS provider.

        Args:
            provider_name: Name of the provider instance
            config: Provider-specific configuration
            config_manager: Configuration manager instance
            log_manager: Logging manager instance
        """
        self._name = provider_name
        self._config = config
        self._config_manager = config_manager
        self._log_manager = log_manager
        self._logger = log_manager.get_logger(f"aws_provider_{provider_name}")
        self._enabled = config.get("enabled", True)  # Default to enabled if not specified

        # Load credentials
        self._credentials = self._load_credentials()

        # Initialize provider if enabled
        self._provider = None
        if self.is_enabled():
            self._initialize_provider()

    @property
    def name(self) -> str:
        """Get the provider name."""
        return self._name

    @property
    def provider_type(self) -> str:
        """Get the provider type."""
        return "aws"

    def is_enabled(self) -> bool:
        """Check if the provider is enabled."""
        return self._enabled

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration."""
        return self._config

    def get_provider(self) -> Optional[aws.Provider]:
        """Get the Pulumi AWS provider instance."""
        return self._provider

    def _load_credentials(self) -> Dict[str, Any]:
        """Load AWS credentials with fallback mechanism.

        Order of precedence:
        1. Explicit credentials from Pulumi stack config
        2. Environment variables
        3. Ambient credentials (default profile or instance role)
        """
        # 1. Try to get from explicit config
        if "credentials" in self._config:
            self._logger.info("Using AWS credentials from explicit configuration")
            return {
                "access_key": self._config["credentials"].get("accessKey"),
                "secret_key": self._config["credentials"].get("secretKey"),
                "session_token": self._config["credentials"].get("sessionToken"),
            }

        # 2. Try to get from environment variables
        if os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"):
            self._logger.info("Using AWS credentials from environment variables")
            return {
                "access_key": os.environ.get("AWS_ACCESS_KEY_ID"),
                "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
                "session_token": os.environ.get("AWS_SESSION_TOKEN"),
            }

        # 3. Use ambient credentials (default profile or instance role)
        # Let Pulumi/AWS handle this automatically
        self._logger.info("Using ambient AWS credentials (default profile or instance role)")
        return {}

    def _initialize_provider(self) -> None:
        """Initialize the AWS provider."""
        try:
            # Create provider options
            provider_args = {}

            # Region is required
            if "region" in self._config:
                provider_args["region"] = self._config["region"]
            else:
                # Default to us-east-1 if not specified
                provider_args["region"] = "us-east-1"
                self._logger.warning(f"No region specified for AWS provider {self._name}, using default: us-east-1")

            # Add credentials if available
            if self._credentials:
                if "access_key" in self._credentials and self._credentials["access_key"]:
                    provider_args["access_key"] = self._credentials["access_key"]
                if "secret_key" in self._credentials and self._credentials["secret_key"]:
                    provider_args["secret_key"] = self._credentials["secret_key"]
                if "session_token" in self._credentials and self._credentials["session_token"]:
                    provider_args["token"] = self._credentials["session_token"]

            # Add other provider options
            if "profile" in self._config:
                provider_args["profile"] = self._config["profile"]

            # Initialize the provider
            self._provider = aws.Provider(
                f"aws-{self._name}",
                **provider_args
            )

            self._logger.info(f"Successfully initialized AWS provider: {self._name}")

        except Exception as e:
            self._logger.error(f"Failed to initialize AWS provider {self._name}: {str(e)}")
            # Even though initialization failed, we don't want to crash the whole program
            # Set enabled to False to indicate the provider is not available
            self._enabled = False


def create_aws_provider(provider_name: str, **kwargs) -> AwsProvider:
    """Create an AWS provider instance.

    Args:
        provider_name: Name of the provider instance
        **kwargs: Additional parameters for the provider

    Returns:
        An AWS provider instance
    """
    return AwsProvider(provider_name, **kwargs)
```

#### 9.3.3 Configuration Schema (`config/schema.py`)

```python
# src/providers/aws/config/schema.py

"""AWS Provider configuration schema."""

AWS_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "enabled": {
            "type": "boolean",
            "description": "Whether the AWS provider is enabled",
            "default": False
        },
        "region": {
            "type": "string",
            "description": "AWS region for the default provider",
            "default": "us-east-1"
        },
        "profile": {
            "type": "string",
            "description": "AWS profile to use"
        },
        "tags": {
            "type": "object",
            "description": "Default tags for all AWS resources",
            "additionalProperties": {
                "type": "string"
            }
        },
        "credentials": {
            "type": "object",
            "description": "AWS credentials (only used if environment variables are not set)",
            "properties": {
                "accessKey": {
                    "type": "string",
                    "description": "AWS access key ID"
                },
                "secretKey": {
                    "type": "string",
                    "description": "AWS secret access key"
                },
                "sessionToken": {
                    "type": "string",
                    "description": "AWS session token (optional)"
                }
            },
            "required": ["accessKey", "secretKey"]
        },
        "providers": {
            "type": "object",
            "description": "Named AWS providers configuration",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Whether this named provider is enabled",
                        "default": True
                    },
                    "region": {
                        "type": "string",
                        "description": "AWS region for this provider"
                    },
                    "profile": {
                        "type": "string",
                        "description": "AWS profile to use for this provider"
                    },
                    "tags": {
                        "type": "object",
                        "description": "Tags for resources created with this provider",
                        "additionalProperties": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "services": {
            "type": "object",
            "description": "Service-specific configurations",
            "properties": {
                "s3": {
                    "type": "object",
                    "description": "S3 service configuration",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether S3 resources are enabled",
                            "default": True
                        },
                        "defaultBucketConfig": {
                            "type": "object",
                            "description": "Default configuration for S3 buckets",
                            "properties": {
                                "versioning": {
                                    "type": "boolean",
                                    "description": "Whether versioning is enabled by default",
                                    "default": False
                                },
                                "encryption": {
                                    "type": "boolean",
                                    "description": "Whether encryption is enabled by default",
                                    "default": True
                                }
                            }
                        }
                    }
                },
                "ec2": {
                    "type": "object",
                    "description": "EC2 service configuration",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Whether EC2 resources are enabled",
                            "default": True
                        },
                        "defaultInstanceType": {
                            "type": "string",
                            "description": "Default EC2 instance type",
                            "default": "t3.micro"
                        }
                    }
                }
            }
        }
    }
}
```

### 9.4 Testing the Core Module

Example test for provider discovery:

```python
# tests/unit/core/providers/test_provider_discovery.py

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import importlib

# Import the module to test
from core.providers.provider_discovery import ProviderDiscovery


class TestProviderDiscovery(unittest.TestCase):
    """Tests for the ProviderDiscovery class."""

    def setUp(self):
        """Set up test fixtures."""
        self.log_manager = MagicMock()
        self.log_manager.get_logger.return_value = MagicMock()
        self.discovery = ProviderDiscovery(self.log_manager)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    def test_discover_provider_modules_empty(self, mock_iterdir, mock_is_dir, mock_exists):
        """Test discovering provider modules when no modules are present."""
        # Mock the directory exists and is a directory
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Mock no directories found
        mock_iterdir.return_value = []

        # Call the method
        result = self.discovery.discover_provider_modules()

        # Assert no provider modules were found
        self.assertEqual(result, [])

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.iterdir')
    @patch('importlib.import_module')
    def test_discover_provider_modules_valid(self, mock_import, mock_iterdir, mock_is_dir, mock_exists):
        """Test discovering valid provider modules."""
        # Mock the directory exists and is a directory
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Create mock directories for AWS and Azure providers
        aws_dir = MagicMock(spec=Path)
        aws_dir.name = "aws"
        aws_dir.is_dir.return_value = True
        aws_dir.__truediv__.return_value.exists.return_value = True

        azure_dir = MagicMock(spec=Path)
        azure_dir.name = "azure"
        azure_dir.is_dir.return_value = True
        azure_dir.__truediv__.return_value.exists.return_value = True

        # Mock directories found
        mock_iterdir.return_value = [aws_dir, azure_dir]

        # Mock successful imports with PROVIDER_NAME attribute
        aws_module = MagicMock()
        aws_module.PROVIDER_NAME = "aws"

        azure_module = MagicMock()
        azure_module.PROVIDER_NAME = "azure"

        mock_import.side_effect = [aws_module, azure_module]

        # Call the method
        result = self.discovery.discover_provider_modules()

        # Assert correct provider modules were found
        self.assertEqual(set(result), {"aws", "azure"})

        # Assert the modules were stored
        self.assertEqual(self.discovery.get_provider_modules()["aws"], aws_module)
        self.assertEqual(self.discovery.get_provider_modules()["azure"], azure_module)


if __name__ == '__main__':
    unittest.main()
```
