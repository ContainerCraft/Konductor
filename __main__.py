# /__main__.py
"""
Konductor Infrastructure as Code Platform

This is the main entry point for the Konductor platform.
"""

import sys
from pulumi import log

from modules.core.initialization import initialize_pulumi
from modules.core.config import ConfigManager
from modules.core.deployment import DeploymentManager
from modules.core.metadata import export_compliance_metadata


def main() -> None:
    """
    Main entry point for Konductor's Pulumi Python Infrastructure as Code.

    Raises:
        SystemExit: With code 1 on error, implicit 0 on success
    """
    try:
        # Initialize Pulumi
        init_config = initialize_pulumi()

        # Initialize Config Manager
        config_manager = ConfigManager()

        # Get enabled modules
        modules_to_deploy = config_manager.get_enabled_modules()

        # Deploy Modules
        if modules_to_deploy:
            log.info(f"Deploying modules: {modules_to_deploy}")
            deployment_manager = DeploymentManager(init_config, config_manager)
            deployment_manager.deploy_modules(modules_to_deploy)
        else:
            # Log and proceed with core IaC execution even if no modules are deployed
            log.info("No modules to deploy.. Proceeding with core IaC execution...")

        # Ensure Git metadata is collected
        from modules.core.git import collect_git_info

        git_info = collect_git_info()

        # Export compliance metadata (which now includes Git and AWS metadata)
        export_compliance_metadata()

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
