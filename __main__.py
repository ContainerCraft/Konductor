# ./__main__.py
"""
Konductor Infrastructure as Code Platform

This is the main entry point for the Konductor platform.
"""

import sys
from pulumi import log, export
import pulumi
from typing import NoReturn

from modules.core.initialization import initialize_pulumi
from modules.core.config import get_enabled_modules, get_stack_outputs
from modules.core.metadata import setup_global_metadata
from modules.core.deployment import DeploymentManager

def main() -> NoReturn:
    """
    Main entry point for Konductor's Pulumi Python Infrastructure as Code (IaC).

    Raises:
        SystemExit: With code 1 on error, implicit 0 on success
    """
    try:
        # Initialize
        init_config = initialize_pulumi()
        setup_global_metadata(init_config)

        # Get enabled modules
        modules_to_deploy = get_enabled_modules(init_config.config)
        if not modules_to_deploy:
            log.info("No modules to deploy")
            return

        # Deploy
        deployment_manager = DeploymentManager(init_config)
        deployment_manager.deploy_modules(modules_to_deploy)

        # Export results
        stack_outputs = get_stack_outputs(init_config)
        export("outputs", stack_outputs)

    except Exception as e:
        log.error(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
