# konductor/__main__.py
"""
Konductor Infrastructure as Code Platform

This is the main entry point for the Konductor platform.
"""

import sys
from pulumi import log

from core.initialization import initialize_pulumi
from core.config import get_enabled_modules
from core.metadata import setup_global_metadata
from core.deployment import DeploymentManager

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
        log.info(f"Deploying modules: {', '.join(modules_to_deploy)}")

        # Create a DeploymentManager with the initialized configuration
        deployment_manager = DeploymentManager(init_config)

        # Deploy the enabled modules
        deployment_manager.deploy_modules(modules_to_deploy)

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
