# pulumi/core/metadata.py
# TODO:
# - enhance with support for propagation of labels annotations on AWS resources
# - enhance by adding additional data to global tag / label / annotation metadata
# - support adding git release semver to global tag / label / annotation metadata

"""
Metadata Management Module

This module manages global metadata, labels, and annotations.
It includes functions to generate compliance and Git-related metadata.
"""

import os
import re
import git
import json
import semver
import threading
from typing import Dict, Optional

from pulumi import log

from .types import ComplianceConfig

# Singleton class to manage global metadata
# Globals are correctly chosen to enforce consistency across all modules and resources
# This class is thread-safe and used to store global labels and annotations
class MetadataSingleton:
    _instance = None
    __lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls.__lock:
                if not cls._instance:
                    cls._instance = super(MetadataSingleton, cls).__new__(cls)
                    cls._instance._data = {"_global_labels": {}, "_global_annotations": {}}
        return cls._instance

def set_global_labels(labels: Dict[str, str]):
    """
    Sets global labels.

    Args:
        labels (Dict[str, str]): The global labels.
    """
    MetadataSingleton()._data["_global_labels"] = labels

def set_global_annotations(annotations: Dict[str, str]):
    """
    Sets global annotations.

    Args:
        annotations (Dict[str, str]): The global annotations.
    """
    MetadataSingleton()._data["_global_annotations"] = annotations

def get_global_labels() -> Dict[str, str]:
    """
    Retrieves global labels.

    Returns:
        Dict[str, str]: The global labels.
    """
    return MetadataSingleton()._data["_global_labels"]

def get_global_annotations() -> Dict[str, str]:
    """
    Retrieves global annotations.

    Returns:
        Dict[str, str]: The global annotations.
    """
    return MetadataSingleton()._data["_global_annotations"]

def generate_git_labels(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates git-related labels suitable for AWS tags.

    Args:
        git_info (Dict[str, str]): The Git information.

    Returns:
        Dict[str, str]: The git-related labels.
    """
    flattened_git_info = flatten_dict(git_info)

    # Sanitize keys and values to conform to AWS tag requirements
    sanitized_labels = {}
    for key, value in flattened_git_info.items():
        sanitized_key = sanitize_tag_key(f"git.{key}")
        sanitized_value = sanitize_tag_value(value)
        sanitized_labels[sanitized_key] = sanitized_value

    return sanitized_labels

def generate_git_annotations(git_info: Dict[str, str]) -> Dict[str, str]:
    """
    Generates git-related annotations.

    Args:
        git_info (Dict[str, str]): The Git information.

    Returns:
        Dict[str, str]: The git-related annotations.
    """
    return {
        "git.remote": git_info.get("remote", ""),
        "git.commit.full": git_info.get("commit", ""),
        "git.branch": git_info.get("branch", "")
    }

def generate_compliance_labels(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance labels based on the given compliance configuration.

    Args:
        compliance_config (ComplianceConfig): The compliance configuration object.

    Returns:
        Dict[str, str]: A dictionary of compliance labels.
    """
    compliance_dict = compliance_config.dict()
    flattened_compliance = flatten_dict(compliance_dict, list_sep=':')

    sanitized_labels = {}
    for key, value in flattened_compliance.items():
        sanitized_key = sanitize_tag_key(key)
        sanitized_value = sanitize_tag_value(value)
        sanitized_labels[sanitized_key] = sanitized_value

    return sanitized_labels

def generate_compliance_annotations(compliance_config: ComplianceConfig) -> Dict[str, str]:
    """
    Generates compliance annotations based on the given compliance configuration.

    Args:
        compliance_config (ComplianceConfig): The compliance configuration object.

    Returns:
        Dict[str, str]: A dictionary of compliance annotations.
    """

    # TODO: enhance if logic to improve efficiency, DRY, readability and maintainability
    annotations = {}
    if compliance_config.fisma.level:
        annotations['compliance.fisma.level'] = compliance_config.fisma.level
    if compliance_config.fisma.ato:
        annotations['compliance.fisma.ato'] = json.dumps(compliance_config.fisma.ato)
    if compliance_config.nist.controls:
        annotations['compliance.nist.controls'] = json.dumps(compliance_config.nist.controls)
    if compliance_config.nist.auxiliary:
        annotations['compliance.nist.auxiliary'] = json.dumps(compliance_config.nist.auxiliary)
    if compliance_config.nist.exceptions:
        annotations['compliance.nist.exceptions'] = json.dumps(compliance_config.nist.exceptions)
    return annotations

# Function to sanitize a label value to comply with Kubernetes `label` naming conventions
# https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
# TODO:
# - retool this feature as a more efficient implementation in `collect_git_info()` and related functions.
def sanitize_label_value(value: str) -> str:
    """
    Sanitizes a label value to comply with Kubernetes naming conventions.

    Args:
        value (str): The value to sanitize.

    Returns:
        str: The sanitized value.
    """
    value = value.lower()
    sanitized = re.sub(r'[^a-z0-9_.-]', '-', value)
    sanitized = re.sub(r'^[^a-z0-9]+', '', sanitized)
    sanitized = re.sub(r'[^a-z0-9]+$', '', sanitized)
    return sanitized[:63]

def flatten_dict(data, parent_key='', sep='.', list_sep=':') -> Dict[str, str]:
    """
    Flattens a nested dictionary into a single-level dictionary with concatenated keys.

    Args:
        data (dict): The dictionary to flatten.
        parent_key (str): The base key string.
        sep (str): The separator between keys.
        list_sep (str): The separator between list items.

    Returns:
        Dict[str, str]: The flattened dictionary.
    """
    items = []
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
        key (str): The key to sanitize.

    Returns:
        str: The sanitized key.
    """
    # AWS tag key must be 1-128 Unicode characters
    sanitized = re.sub(r'[^a-zA-Z0-9\s_.:/=+\-@]', '-', key)
    return sanitized[:128]

def sanitize_tag_value(value: str) -> str:
    """
    Sanitizes a string to be used as an AWS tag value.

    Args:
        value (str): The value to sanitize.

    Returns:
        str: The sanitized value.
    """
    # AWS tag value must be 0-256 Unicode characters
    # Include colons ':' in the allowed characters
    sanitized = re.sub(r'[^a-zA-Z0-9\s_./:=+\-@]', '-', value)
    return sanitized[:256]

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
        'remote': 'N/A',
        'branch': 'N/A',
        'commit': 'N/A',
        'commit_short': 'N/A',
        'commit_date': 'N/A',
        'latest_tag': 'N/A',
        'latest_release': 'N/A',
        'dirty': 'false'
    }

    try:
        # Initialize repo object
        repo = git.Repo(search_parent_directories=True)

        # Get remote URL (try multiple methods)
        try:
            remote_url = get_remote_url(repo)
            git_info['remote'] = remote_url
        except Exception as e:
            log.warn(f"Failed to get remote URL: {str(e)}")

        # Get current branch
        try:
            git_info['branch'] = repo.active_branch.name
        except TypeError:
            # Handle detached HEAD state
            git_info['branch'] = 'HEAD'
        except Exception as e:
            log.warn(f"Failed to get branch name: {str(e)}")

        # Get commit information
        try:
            commit = repo.head.commit
            git_info.update({
                'commit': commit.hexsha,
                'commit_short': commit.hexsha[:8],
                'commit_date': commit.committed_datetime.isoformat(),
            })
        except Exception as e:
            log.warn(f"Failed to get commit information: {str(e)}")

        # Get latest tag and release information
        try:
            latest_tag = get_latest_semver_tag(repo)
            if latest_tag:
                git_info['latest_tag'] = latest_tag
                git_info['latest_release'] = str(semver.VersionInfo.parse(latest_tag.lstrip('v')))
        except Exception as e:
            log.warn(f"Failed to get tag/release information: {str(e)}")

        # Check if working tree is dirty
        git_info['dirty'] = str(repo.is_dirty()).lower()

        log.info(f"Successfully collected git info: {git_info}")

    except git.exc.InvalidGitRepositoryError:
        log.warn("Not a git repository. Using default values.")
    except Exception as e:
        log.warn(f"Error collecting git information: {str(e)}")
        log.warn("Using default values for git information")

    return git_info

def get_remote_url(repo: git.Repo) -> str:
    """
    Gets the remote URL using multiple fallback methods.

    Args:
        repo: GitPython Repo object

    Returns:
        str: Remote URL or 'N/A' if not found
    """
    # Try getting from origin remote
    try:
        return next(remote.url for remote in repo.remotes if remote.name == 'origin')
    except (StopIteration, AttributeError):
        pass

    # Try getting from git config
    try:
        return repo.git.config('--get', 'remote.origin.url')
    except git.exc.GitCommandError:
        pass

    # Try environment variables (useful in CI/CD)
    for env_var in ['CI_REPOSITORY_URL', 'GITHUB_REPOSITORY', 'GIT_URL']:
        if url := os.getenv(env_var):
            return url

    return 'N/A'

def get_latest_semver_tag(repo: git.Repo) -> Optional[str]:
    """
    Gets the latest semantic version tag from the repository.
    Handles both 'v' prefixed and non-prefixed tags.

    Args:
        repo: GitPython Repo object

    Returns:
        Optional[str]: Latest semver tag or None if no valid tags found
    """
    try:
        # Get all tags
        tags = [str(tag) for tag in repo.tags]

        # Filter for semver tags (with or without 'v' prefix)
        semver_tags = []
        for tag in tags:
            # Remove 'v' prefix if present
            version_str = tag.lstrip('v')
            try:
                # Parse version and add to list if valid
                version = semver.VersionInfo.parse(version_str)
                semver_tags.append((version, tag))
            except ValueError:
                continue

        # Return the latest version tag if any found
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
        # Convert to lowercase and replace invalid characters
        sanitized_value = re.sub(r'[^a-z0-9-._]', '-', str(value).lower())

        # Trim to maximum allowed length (63 chars for k8s labels)
        sanitized_value = sanitized_value[:63]

        # Remove leading/trailing non-alphanumeric characters
        sanitized_value = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', sanitized_value)

        sanitized[key] = sanitized_value

    return sanitized
