# pulumi/core/metadata.py

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It includes functions to generate compliance and Git-related metadata.
"""

import os
import re
import json
import semver
import threading
from typing import Dict, Optional, ClassVar, Any, List, Tuple
from git import Repo, GitCommandError
from pulumi import log

from .types import ComplianceConfig, InitializationConfig

class MetadataSingleton:
    """
    Thread-safe singleton class to manage global metadata.
    Ensures consistent labels and annotations across all resources.
    """
    _instance: ClassVar[Optional['MetadataSingleton']] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        """Initialize metadata storage."""
        self._global_labels: Dict[str, str] = {}
        self._global_annotations: Dict[str, str] = {}

    def __new__(cls) -> 'MetadataSingleton':
        """Ensure only one instance is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.__init__()
                    cls._instance = instance
        return cls._instance

    @property
    def global_labels(self) -> Dict[str, str]:
        """Get global labels."""
        return self._global_labels.copy()

    @property
    def global_annotations(self) -> Dict[str, str]:
        """Get global annotations."""
        return self._global_annotations.copy()

    def set_labels(self, labels: Dict[str, str]) -> None:
        """Set global labels."""
        self._global_labels = labels.copy()

    def set_annotations(self, annotations: Dict[str, str]) -> None:
        """Set global annotations."""
        self._global_annotations = annotations.copy()


def set_global_labels(labels: Dict[str, str]) -> None:
    """
    Sets global labels.

    Args:
        labels: The global labels to set.
    """
    MetadataSingleton().set_labels(labels)


def set_global_annotations(annotations: Dict[str, str]) -> None:
    """
    Sets global annotations.

    Args:
        annotations: The global annotations to set.
    """
    MetadataSingleton().set_annotations(annotations)


def get_global_labels() -> Dict[str, str]:
    """
    Retrieves global labels.

    Returns:
        Dict[str, str]: The global labels.
    """
    return MetadataSingleton().global_labels


def get_global_annotations() -> Dict[str, str]:
    """
    Retrieves global annotations.

    Returns:
        Dict[str, str]: The global annotations.
    """
    return MetadataSingleton().global_annotations


def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates git-related labels suitable for AWS tags.

    Args:
        git_info: The Git information.

    Returns:
        Dict[str, str]: The git-related labels.
    """
    flattened_git_info = flatten_dict(git_info)
    sanitized_labels: Dict[str, str] = {}

    for key, value in flattened_git_info.items():
        sanitized_key = sanitize_tag_key(f"git.{key}")
        sanitized_value = sanitize_tag_value(str(value))
        sanitized_labels[sanitized_key] = sanitized_value

    return sanitized_labels


def generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates git-related annotations.

    Args:
        git_info: The Git information.

    Returns:
        Dict[str, str]: The git-related annotations.
    """
    return {
        "git.remote": git_info.get("remote", ""),
        "git.commit.full": git_info.get("commit", ""),
        "git.branch": git_info.get("branch", ""),
    }


def generate_compliance_labels(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance labels based on the given compliance configuration.

    Args:
        compliance_config: The compliance configuration object.

    Returns:
        Dict[str, str]: A dictionary of compliance labels.
    """
    compliance_dict = compliance_config.dict()
    flattened_compliance = flatten_dict(compliance_dict, list_sep=":")
    sanitized_labels: Dict[str, str] = {}

    for key, value in flattened_compliance.items():
        sanitized_key = sanitize_tag_key(key)
        sanitized_value = sanitize_tag_value(str(value))
        sanitized_labels[sanitized_key] = sanitized_value

    return sanitized_labels


def generate_compliance_annotations(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance annotations based on the given compliance configuration.

    Args:
        compliance_config: The compliance configuration object.

    Returns:
        Dict[str, str]: A dictionary of compliance annotations.
    """
    annotations: Dict[str, str] = {}

    if compliance_config.fisma.level:
        annotations["compliance.fisma.level"] = compliance_config.fisma.level
    if compliance_config.fisma.ato:
        annotations["compliance.fisma.ato"] = json.dumps(compliance_config.fisma.ato)
    if compliance_config.nist.controls:
        annotations["compliance.nist.controls"] = json.dumps(compliance_config.nist.controls)
    if compliance_config.nist.auxiliary:
        annotations["compliance.nist.auxiliary"] = json.dumps(compliance_config.nist.auxiliary)
    if compliance_config.nist.exceptions:
        annotations["compliance.nist.exceptions"] = json.dumps(compliance_config.nist.exceptions)

    return annotations


def sanitize_label_value(value: str) -> str:
    """
    Sanitizes a label value to comply with Kubernetes naming conventions.

    Args:
        value: The value to sanitize.

    Returns:
        str: The sanitized value.
    """
    value = value.lower()
    sanitized = re.sub(r"[^a-z0-9_.-]", "-", value)
    sanitized = re.sub(r"^[^a-z0-9]+", "", sanitized)
    sanitized = re.sub(r"[^a-z0-9]+$", "", sanitized)
    return sanitized[:63]


def flatten_dict(
    data: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
    list_sep: str = ":"
) -> Dict[str, str]:
    """
    Flattens a nested dictionary into a single-level dictionary with concatenated keys.

    Args:
        data: The dictionary to flatten.
        parent_key: The base key string.
        sep: The separator between keys.
        list_sep: The separator between list items.

    Returns:
        Dict[str, str]: The flattened dictionary.
    """
    items: List[Tuple[str, str]] = []

    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep, list_sep=list_sep).items())
        elif isinstance(v, list):
            items.append((new_key, list_sep.join(map(str, v))))
        elif v is not None:
            items.append((new_key, str(v)))

    return dict(items)


def sanitize_tag_key(key: str) -> str:
    """
    Sanitizes a string to be used as an AWS tag key.

    Args:
        key: The key to sanitize.

    Returns:
        str: The sanitized key.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9\s_.:/=+\-@]", "-", key)
    return sanitized[:128]


def sanitize_tag_value(value: str) -> str:
    """
    Sanitizes a string to be used as an AWS tag value.

    Args:
        value: The value to sanitize.

    Returns:
        str: The sanitized value.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9\s_./:=+\-@]", "-", value)
    return sanitized[:256]


def get_remote_url(repo: Repo) -> str:
    """
    Gets the remote URL using multiple fallback methods.

    Args:
        repo: GitPython Repo object

    Returns:
        str: Remote URL or 'N/A' if not found
    """
    try:
        return next(remote.url for remote in repo.remotes if remote.name == "origin")
    except (StopIteration, AttributeError, GitCommandError) as e:
        log.warn(f"Failed to get remote URL via remotes: {str(e)}")

    try:
        return repo.git.config("--get", "remote.origin.url")
    except GitCommandError as e:
        log.warn(f"Failed to get remote URL via git config: {str(e)}")

    for env_var in ["CI_REPOSITORY_URL", "GITHUB_REPOSITORY", "GIT_URL"]:
        if url := os.getenv(env_var):
            return url

    return "N/A"


def get_latest_semver_tag(repo: Repo) -> Optional[str]:
    """
    Gets the latest semantic version tag from the repository.

    Args:
        repo: GitPython Repo object

    Returns:
        Optional[str]: Latest semver tag or None if no valid tags found
    """
    try:
        tags = [str(tag) for tag in repo.tags]
        semver_tags: List[Tuple[semver.VersionInfo, str]] = []

        for tag in tags:
            version_str = tag.lstrip("v")
            try:
                version = semver.VersionInfo.parse(version_str)
                semver_tags.append((version, tag))
            except (ValueError, GitCommandError) as e:
                log.warn(f"Error parsing tag {tag}: {str(e)}")
                continue

        if semver_tags:
            return sorted(semver_tags, key=lambda x: x[0])[-1][1]

    except Exception as e:
        log.warn(f"Error parsing semver tags: {str(e)}")

    return None


def collect_git_info() -> Dict[str, str]:
    """
    Collects Git repository information using GitPython.
    Includes repository details, latest tag/release version, and commit information.
    Falls back gracefully with informative logging.

    Returns:
        Dict[str, str]: Git information including:
            - remote: Repository remote URL
            - branch: Current branch name
            - commit: Current commit hash
            - commit_short: Shortened commit hash
            - commit_date: Commit timestamp
            - latest_tag: Latest semver tag
            - latest_release: Latest release version
            - dirty: Whether working tree has uncommitted changes
    """
    git_info = {
        "remote": "N/A",
        "branch": "N/A",
        "commit": "N/A",
        "commit_short": "N/A",
        "commit_date": "N/A",
        "latest_tag": "N/A",
        "latest_release": "N/A",
        "dirty": "false",
    }

    try:
        repo = Repo(search_parent_directories=True)

        try:
            remote_url = get_remote_url(repo)
            git_info["remote"] = remote_url
        except Exception as e:
            log.warn(f"Failed to get remote URL: {str(e)}")

        try:
            git_info["branch"] = repo.active_branch.name
        except (TypeError, GitCommandError) as e:
            git_info["branch"] = "HEAD"
            log.warn(f"Failed to get branch name: {str(e)}")

        try:
            commit = repo.head.commit
            git_info.update({
                "commit": commit.hexsha,
                "commit_short": commit.hexsha[:8],
                "commit_date": commit.committed_datetime.isoformat(),
            })
        except Exception as e:
            log.warn(f"Failed to get commit information: {str(e)}")

        try:
            latest_tag = get_latest_semver_tag(repo)
            if latest_tag:
                git_info["latest_tag"] = latest_tag
                git_info["latest_release"] = str(
                    semver.VersionInfo.parse(latest_tag.lstrip("v"))
                )
        except Exception as e:
            log.warn(f"Failed to get tag/release information: {str(e)}")

        git_info["dirty"] = str(repo.is_dirty()).lower()
        log.info(f"Successfully collected git info: {git_info}")

    except Exception as e:
        log.warn(f"Error collecting git information: {str(e)}")
        log.warn("Using default values for git information")

    return git_info

def get_remote_url(repo: Repo) -> str:
    """
    Gets the remote URL using multiple fallback methods.

    Args:
        repo: GitPython Repo object

    Returns:
        str: Remote URL or 'N/A' if not found
    """
    try:
        return next(remote.url for remote in repo.remotes if remote.name == "origin")
    except (StopIteration, AttributeError, GitCommandError) as e:
        log.warn(f"Failed to get remote URL: {str(e)}")
        pass

    try:
        return repo.git.config("--get", "remote.origin.url")
    except GitCommandError:
        pass

    for env_var in ["CI_REPOSITORY_URL", "GITHUB_REPOSITORY", "GIT_URL"]:
        if url := os.getenv(env_var):
            return url

    return "N/A"


def get_latest_semver_tag(repo: Repo) -> Optional[str]:
    """
    Gets the latest semantic version tag from the repository.
    """
    try:
        tags = [str(tag) for tag in repo.tags]
        semver_tags = []

        for tag in tags:
            version_str = tag.lstrip("v")
            try:
                version = semver.VersionInfo.parse(version_str)
                semver_tags.append((version, tag))
            except (ValueError, GitCommandError) as e:
                log.warn(f"Error parsing tag {tag}: {str(e)}")
                continue

        if semver_tags:
            return sorted(semver_tags, key=lambda x: x[0])[-1][1]

    except Exception as e:
        log.warn(f"Error parsing semver tags: {str(e)}")

    return None


def sanitize_git_info(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitizes git information for use in resource tags/labels.
    Ensures values meet length and character requirements.

    Args:
        git_info: Raw git information dictionary

    Returns:
        Dict[str, str]: Sanitized git information
    """
    sanitized = {}

    for key, value in git_info.items():
        sanitized_value = re.sub(r"[^a-z0-9-._]", "-", str(value).lower())
        sanitized_value = sanitized_value[:63]
        sanitized_value = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", sanitized_value)
        sanitized[key] = sanitized_value

    return sanitized


def generate_aws_tags(
    git_info: Dict[str, str],
    compliance_config: ComplianceConfig
) -> Dict[str, str]:
    """Generate AWS-specific tags."""
    tags = {
        **generate_git_labels(git_info),
        **generate_compliance_labels(compliance_config),
        "managed-by": "pulumi",
        "automation": "konductor"
    }

    # Ensure tag values meet AWS requirements
    return {k: sanitize_tag_value(str(v)) for k, v in tags.items()}

def setup_global_metadata(init_config: InitializationConfig) -> None:
    """
    Initialize global metadata for resources.

    Args:
        init_config: Initialization configuration object
    """
    try:
        # Collect git information
        git_info = collect_git_info()
        init_config.git_info = git_info

        # Set global resource metadata
        set_global_labels(init_config.metadata.labels)
        set_global_annotations(init_config.metadata.annotations)

    except Exception as e:
        log.error(f"Failed to setup global metadata: {str(e)}")
        raise
