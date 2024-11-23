# ../konductor/__main__.py
"""
Konductor Infrastructure as Code Platform

This is the main entry point for the Konductor platform.
"""

import sys
from pulumi import log, export
import pulumi

from modules.core.initialization import initialize_pulumi
from modules.core.config import get_enabled_modules, get_stack_outputs
from modules.core.metadata import setup_global_metadata
from modules.core.deployment import DeploymentManager

def main() -> None:
    """
    Main entry point for Konductor's Pulumi Python Infrastructure as Code (IaC).
    """
    try:
        # Initialize Pulumi and load configuration
        init_config = initialize_pulumi()

        # Set up global metadata
        setup_global_metadata(init_config)

        # Get the list of enabled modules from the configuration
        modules_to_deploy = get_enabled_modules(init_config.config)

        if not modules_to_deploy:
            log.info("No modules to deploy.")
        else:
            log.info(f"Deploying modules: {', '.join(modules_to_deploy)}")

            # Create a DeploymentManager with the initialized configuration
            deployment_manager = DeploymentManager(init_config)

            # Deploy the enabled modules
            deployment_manager.deploy_modules(modules_to_deploy)

        # Generate and export stack outputs
        try:
            stack_outputs = get_stack_outputs(init_config)

            # Export each section separately for better organization
            export("compliance", stack_outputs["compliance"])
            export("config", stack_outputs["config"])
            export("k8s_app_versions", stack_outputs["k8s_app_versions"])

            log.info("Successfully exported stack outputs")
        except Exception as e:
            log.error(f"Failed to export stack outputs: {str(e)}")
            raise

    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
