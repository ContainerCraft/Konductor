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

import re
import json
import threading
import subprocess
import dataclasses
from typing import Dict, Any

import pulumi
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

# Function to collect Git repository information
# TODO: re-implement this function to use the GitPython library or other more pythonic approach
# TODO: add support for fetching and returning the latest git release semver
def collect_git_info() -> Dict[str, str]:
    """
    Collects Git repository information.

    Returns:
        Dict[str, str]: The Git information.
    """
    try:
        remote = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.STDOUT).strip().decode('utf-8')
        return {'remote': remote, 'branch': branch, 'commit': commit}
    except subprocess.CalledProcessError as e:
        log.error(f"Error fetching git information: {e}")
        return {'remote': 'N/A', 'branch': 'N/A', 'commit': 'N/A'}

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
    # Convert the ComplianceConfig to a dictionary
    compliance_dict = compliance_config.dict()
    # Flatten the nested compliance dictionary
    flattened_compliance = flatten_dict(compliance_dict)

    # Sanitize keys and values to conform to AWS tag requirements
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

def flatten_dict(data, parent_key='', sep='.') -> Dict[str, str]:
    """
    Flattens a nested dictionary into a single-level dictionary with concatenated keys.

    Args:
        data (dict): The dictionary to flatten.
        parent_key (str): The base key string.
        sep (str): The separator between keys.

    Returns:
        Dict[str, str]: The flattened dictionary.
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Always recurse into dictionaries
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert list to comma-separated string
            items.append((new_key, ','.join(map(str, v))))
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
    sanitized = re.sub(r'[^a-zA-Z0-9\s_,.:/=+\-@]', '-', value)
    return sanitized[:256]
