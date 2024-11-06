#!/usr/bin/env python3
"""
Konductor Infrastructure as Code Platform

This is the main entry point for the Konductor platform, which provides:
- Multi-cloud infrastructure deployment
- Compliance-driven resource management
- Modular infrastructure components
- GitOps-ready configuration

Usage:
    pulumi up [stack-name]
    pulumi preview [stack-name]
    pulumi destroy [stack-name]
"""

import sys
from typing import Dict, Any, List
import pulumi
from pulumi import log

from core.config import (
    get_enabled_modules,
    load_default_versions,
    initialize_config,
    validate_module_config
)
from core.deployment import (
    initialize_pulumi,
    deploy_modules,
    DeploymentManager
)
from core.metadata import (
    collect_git_info,
    set_global_labels,
    set_global_annotations,
    setup_global_metadata
)
from core.types import (
    InitializationConfig,
    ComplianceConfig,
    ModuleDeploymentResult
)

def main() -> None:
    """
    Main entry point for Konductor platform.

    Handles:
    - Platform initialization
    - Module deployment
    - Resource management
    - Error handling
    """
    try:
        # Initialize Pulumi
        init = initialize_pulumi()

        # Extract initialization components
        config: pulumi.Config = init.config
        k8s_provider = init.k8s_provider
        default_versions = load_default_versions(config)
        compliance_config = ComplianceConfig.merge(
            config.get_object("compliance") or {}
        )

        # Initialize configuration
        init_config = initialize_config({
            "config": config,
            "stack_name": pulumi.get_stack(),
            "project_name": pulumi.get_project(),
            "default_versions": default_versions,
            "k8s_provider": k8s_provider,
            "compliance_config": compliance_config
        })

        # Setup global metadata
        setup_global_metadata(init_config)

        # Get enabled modules
        modules_to_deploy = get_enabled_modules(config)
        log.info(f"Deploying modules: {', '.join(modules_to_deploy)}")

        # Create deployment manager
        deployment_manager = DeploymentManager(init_config)

        # Deploy modules
        results: Dict[str, ModuleDeploymentResult] = {}
        for module_name in modules_to_deploy:
            try:
                # Validate module configuration
                module_config = config.get_object(module_name) or {}
                validate_module_config(module_name, module_config)

                # Deploy module
                result = deployment_manager.deploy_module(module_name)
                results[module_name] = result

                if not result.success:
                    log.error(f"Failed to deploy module {module_name}: {result.errors}")
                    continue

                # Export module outputs
                pulumi.export(f"{module_name}_version", result.version)
                pulumi.export(f"{module_name}_resources", result.resources)
                pulumi.export(f"{module_name}_metadata", result.metadata)

            except Exception as e:
                log.error(f"Error deploying module {module_name}: {str(e)}")
                results[module_name] = ModuleDeploymentResult(
                    success=False,
                    version="",
                    resources=[],
                    errors=[str(e)]
                )

        # Export global results
        pulumi.export("deployment_results", {
            name: {
                "success": result.success,
                "version": result.version,
                "errors": result.errors
            }
            for name, result in results.items()
        })

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
