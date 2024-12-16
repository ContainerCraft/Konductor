import pulumi

from typing import Dict, Any

from .types import GlobalMetadata
from modules.core.git import collect_git_info


def get_stack_outputs(
    init_config: Dict[str, Any],
    modules_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Collect and assemble stack outputs.
    """
    # Get base metadata
    global_metadata = collect_global_metadata()

    # Build config structure
    config = {
        "metadata": {
            "globalLabels": init_config.get("metadata", {}).get("labels", {}),
            "globalAnnotations": init_config.get("metadata", {}).get("annotations", {}),
        },
        "global_metadata": global_metadata,
        "source_repository": {
            "branch": init_config["git_info"].branch_name,
            "commit": init_config["git_info"].commit_hash,
            "remote": init_config["git_info"].remote_url,
        },
    }

    # Add compliance data
    if compliance_config := init_config.get("compliance_config"):
        # Convert compliance config to dict using model's method
        config["compliance"] = compliance_config.model_dump()

    # Add module-specific configs
    for module_name, metadata in modules_metadata.items():
        config[module_name] = metadata

    # Add kubernetes versions
    k8s_versions = {
        name: {version: {} for version in versions}
        for name, versions in init_config.get("versions", {}).items()
        if name in ["cert_manager", "kubevirt"]
    }
    config["k8s_versions"] = k8s_versions

    return {"config": config}


def collect_global_metadata() -> GlobalMetadata:
    """
    Collect global metadata such as project name, stack name, and Git info.

    Returns:
        dict: Global metadata dictionary.
    """
    project_name = pulumi.get_project()
    stack_name = pulumi.get_stack()

    git_info = collect_git_info()
    git_info_dict = git_info.model_dump()

    return {
        "project_name": project_name,
        "stack_name": stack_name,
        **git_info_dict,
    }


def collect_module_metadata(global_metadata: Dict[str, Any], modules_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Merge global metadata with module-specific metadata.
    """
    module_metadata = global_metadata.copy()
    if modules_metadata:
        for module_name, metadata in modules_metadata.items():
            module_metadata[module_name] = metadata
    return module_metadata


def collect_compliance_outputs() -> Dict[str, Any]:
    """
    Collect compliance-related outputs from modules.

    Returns:
        dict: Compliance outputs dictionary.
    """
    return {
        # TODO: Support lists of compliance frameworks and controls based on
        # Pulumi.scip-ops-prod.yaml development specification as pulumi stack
        # config
        "compliance_frameworks": ["NIST", "FISMA"],
        "controls": {
            "AC-2": "<todo_support_lists_of_controls>",
            "AC-3": "<todo_support_lists_of_controls>",
            # Add other controls
        },
        "status": "Compliant",
    }
