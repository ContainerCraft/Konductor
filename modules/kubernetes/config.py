# ./modules/kubernetes/config.py
"""
Kubernetes module configuration.

This module provides the configuration for the Kubernetes module.
"""

from typing import Dict
from core.types import ModuleDefaults

# Default Remote Versions URL, used if no versions are specified in the module config or default_versions.json
DEFAULT_VERSIONS_URL_TEMPLATE = "https://raw.githubusercontent.com/ContainerCraft/Kargo/newfactor/modules/"

# Default module configuration
DEFAULT_MODULE_CONFIG: Dict[str, ModuleDefaults] = {
    "cert_manager": {"enabled": False, "version": None, "config": {}},
    "flux": {"enabled": False, "version": None, "config": {}},
    "crossplane": {"enabled": False, "version": None, "config": {}},
    "prometheus": {"enabled": False, "version": None, "config": {}},
    "kubevirt": {"enabled": False, "version": None, "config": {}},
    "multus": {"enabled": False, "version": None, "config": {}},
    "hostpath_provisioner": {"enabled": False, "version": None, "config": {}},
    "containerized_data_importer": {"enabled": False, "version": None, "config": {}},
}
