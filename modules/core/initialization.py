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
        stack_name = get_stack()
        project_name = get_project()

        # Collect Git metadata
        git_info = collect_git_info()
        log.info(f"Git Info: commit_hash='{git_info.commit_hash}' branch_name='{git_info.branch_name}' remote_url='{git_info.remote_url}'")

        # Load default versions (provide actual default versions as needed)
        default_versions = {}

        # Create the initialization config
        init_config = InitializationConfig(
            pulumi_config=pulumi_config,
            stack_name=stack_name,
            project_name=project_name,
            default_versions=default_versions,
            git_info=git_info,
            metadata={}
        )

        return init_config

    except Exception as e:
        log.error(f"Failed to initialize Pulumi: {str(e)}")
        raise
