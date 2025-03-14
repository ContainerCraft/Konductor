# ./modules/core/stack_outputs.py

"""
Stack Outputs Module

This module collects and assembles stack outputs for `pulumi.export`.
"""

from typing import Dict, Any
import pulumi
from pulumi import log

from .types import (
    InitializationConfig,
    GlobalMetadata,
    StackConfig,
    StackOutputs,
    ComplianceConfig,
    SourceRepository,
    MetadataSingleton,
)
from .git import collect_git_info


def get_stack_outputs(
    init_config: InitializationConfig,
    modules_metadata: Dict[str, Dict[str, Any]],
) -> StackOutputs:
    """
    Collect and assemble stack outputs.

    Args:
        init_config: Initialization configuration
        modules_metadata: Module-specific metadata

    Returns:
        StackOutputs: Consolidated stack outputs
    """
    # Get base metadata
    global_metadata = collect_global_metadata()

    # Get git info
    git_info = collect_git_info()
    source_repo = SourceRepository(
        branch=git_info.branch_name,
        commit=git_info.commit_hash,
        remote=git_info.remote_url,
        tag=git_info.release_tag
    )

    # Build stack config
    stack_config = StackConfig(
        compliance=init_config.compliance_config,
        metadata=GlobalMetadata(
            tags=global_metadata.get("tags", {}),
            labels=global_metadata.get("labels", {}),
            annotations=global_metadata.get("annotations", {})
        ),
        source_repository=source_repo
    )

    # Create stack outputs
    stack_outputs = StackOutputs(
        stack=stack_config,
        secrets=None  # TODO: Implement secrets handling
    )

    # Add module-specific metadata
    for module_name, metadata in modules_metadata.items():
        if metadata:
            log.debug(f"Adding metadata for module: {module_name}")
            # Store module metadata in singleton for future reference
            MetadataSingleton().set_module_metadata(module_name, metadata)

    return stack_outputs


def collect_global_metadata() -> Dict[str, Any]:
    """
    Collect global metadata such as project name, stack name, and Git info.

    Returns:
        Dict[str, Any]: Global metadata dictionary
    """
    metadata = MetadataSingleton()
    return {
        "project_name": pulumi.get_project(),
        "stack_name": pulumi.get_stack(),
        "tags": metadata.global_tags,
        "labels": metadata.global_labels,
        "annotations": metadata.global_annotations,
        "git": metadata.git_metadata,
    }


def collect_module_metadata(
    global_metadata: Dict[str, Any],
    modules_metadata: Dict[str, Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    """
    Merge global metadata with module-specific metadata.

    Args:
        global_metadata: Base metadata dictionary
        modules_metadata: Optional module-specific metadata

    Returns:
        Dict[str, Any]: Combined metadata dictionary
    """
    module_metadata = global_metadata.copy()
    if modules_metadata:
        for module_name, metadata in modules_metadata.items():
            module_metadata[module_name] = metadata
    return module_metadata


def collect_compliance_outputs() -> ComplianceConfig:
    """
    Collect compliance-related outputs from modules.

    Returns:
        ComplianceConfig: Compliance configuration and status
    """
    metadata = MetadataSingleton()
    if compliance_data := metadata.get_module_metadata("compliance"):
        return ComplianceConfig.model_validate(compliance_data)
    return ComplianceConfig.create_default()


def export_stack_outputs(stack_outputs: StackOutputs) -> None:
    """
    Export stack outputs to Pulumi.

    Args:
        stack_outputs: Stack outputs to export
    """
    try:
        pulumi.export("stack_outputs", stack_outputs.model_dump())
        log.info("Successfully exported stack outputs")
    except Exception as e:
        log.error(f"Failed to export stack outputs: {str(e)}")
        raise
