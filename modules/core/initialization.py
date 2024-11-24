# ../konductor/modules/core/initialization.py
import pulumi
from pulumi import Config, get_stack, get_project, log

from modules.core.types import InitializationConfig, GitInfo
from modules.core.git import collect_git_info

def initialize_pulumi() -> InitializationConfig:
    """
    Initializes Pulumi and loads the configuration.

    Returns:
        InitializationConfig: The initialization configuration object.
    """
    try:
        # Load Pulumi configuration
        pulumi_config = Config()

        # Get stack and project names from Pulumi
        stack_name = get_stack()
        project_name = get_project()
        log.info(f"DEBUG: project_name from get_project(): {project_name}")

        # Initialize default metadata structure
        metadata = {
            "labels": {},
            "annotations": {}
        }

        # Create the initialization config
        init_config = InitializationConfig(
            pulumi_config=pulumi_config,
            stack_name=stack_name,
            project_name=project_name,
            default_versions={},
            git_info=collect_git_info(),
            metadata=metadata
        )

        log.info(f"Initialized Pulumi with project: {project_name}, stack: {stack_name}")
        return init_config

    except Exception as e:
        log.error(f"Failed to initialize Pulumi: {str(e)}")
        raise
