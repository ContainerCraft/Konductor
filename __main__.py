# /__main__.py
"""
Konductor Infrastructure as Code Platform

This is the main entry point for the Konductor platform.
"""

from sys import exit
from pulumi import log

from modules.core.initialization import initialize_pulumi
from modules.core.config import ConfigManager
from modules.core.types import setup_global_metadata
from modules.core.deployment import DeploymentManager
from modules.core.metadata import export_compliance_metadata


def main() -> None:
    """
    Main entry point for Konductor's Pulumi Python Infrastructure as Code.
    """
    try:
        log.debug("Starting Konductor initialization")

        # Initialize Pulumi with new type system - this loads ALL config
        init_config = initialize_pulumi()
        log.debug(f"Initialized with git info: {init_config.git_info.model_dump()}")

        # Setup global metadata using new type system
        setup_global_metadata(init_config)
        log.debug("Global metadata setup complete")

        # Initialize Config Manager with the FULL config from init
        config_manager = ConfigManager(init_config.pulumi_config)

        # Get enabled modules and deploy if any are enabled
        if modules_to_deploy := config_manager.get_enabled_modules():
            log.info(f"Deploying modules: {', '.join(modules_to_deploy)}")
            deployment_manager = DeploymentManager(init_config, config_manager)
            deployment_manager.deploy_modules(modules_to_deploy)
        else:
            log.info("No modules enabled - proceeding with core IaC execution...")

        # Export compliance metadata
        export_compliance_metadata()

        log.info("Deployment completed successfully")

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
