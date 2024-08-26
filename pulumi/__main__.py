import os
import requests
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import Provider

from src.lib.kubernetes_api_endpoint import KubernetesApiEndpointIp
from src.cilium.deploy import deploy_cilium
from src.cert_manager.deploy import deploy_cert_manager
from src.openunison.deploy import deploy_openunison
from src.prometheus.deploy import deploy_prometheus
from src.kubernetes_dashboard.deploy import deploy_kubernetes_dashboard
from src.vm.ubuntu import deploy_ubuntu_vm

##################################################################################
# Load the Pulumi Config
config = pulumi.Config()

# Get pulumi stack name
stack_name = pulumi.get_stack()

# Get the pulumi project name
project_name = pulumi.get_project()

##################################################################################
# Get the Kubernetes configuration
kubernetes_config = config.get_object("kubernetes") or {}

# Get Kubeconfig from Pulumi ESC Config
kubeconfig = kubernetes_config.get("kubeconfig")

# Require Kubernetes context set explicitly
kubernetes_context = kubernetes_config.get("context")

# Get the Kubernetes distribution (supports: kind, talos)
kubernetes_distribution = kubernetes_config.get("distribution") or "talos"

# Create a Kubernetes provider instance
k8s_provider = Provider(
    "k8sProvider",
    kubeconfig=kubeconfig,
    context=kubernetes_context
)

versions = {}

##################################################################################
## Enable/Disable Kargo Kubevirt PaaS Infrastructure Modules
##################################################################################

# Utility function to handle config with default "enabled" flag
def get_module_config(module_name):
    module_config = config.get_object(module_name) or {"enabled": "false"}
    module_enabled = str(module_config.get('enabled')).lower() == "true"
    return module_config, module_enabled

# Get configurations and enabled flags
config_cilium, cilium_enabled = get_module_config('cilium')
config_cert_manager, cert_manager_enabled = get_module_config('cert_manager')
config_prometheus, prometheus_enabled = get_module_config('prometheus')
config_openunison, openunison_enabled = get_module_config('openunison')
config_kubernetes_dashboard, kubernetes_dashboard_enabled = get_module_config('kubernetes_dashboard')
config_vm, vm_enabled = get_module_config('vm')

##################################################################################
## Get the Kubernetes API endpoint IP
##################################################################################

# check if kubernetes distribution is "kind" and if so execute get the kubernetes api endpoint ip
if kubernetes_distribution == "kind":
    # Get the Kubernetes API endpoint IP
    k8s_endpoint_ip = KubernetesApiEndpointIp(
        "kubernetes-endpoint-service-address",
        k8s_provider
    )

    # Extract the Kubernetes Endpoint clusterIP
    kubernetes_endpoint_service = pulumi.Output.from_input(k8s_endpoint_ip)
    kubernetes_endpoint_service_address = kubernetes_endpoint_service.endpoint.subsets[0].addresses[0].ip
    pulumi.export(
        "kubernetes-endpoint-service-address",
        kubernetes_endpoint_service_address
    )
else:
    # default to talos k8s endpoint "localhost" when not kind k8s
    kubernetes_endpoint_service_address = "localhost"

##################################################################################
## Core Kargo Kubevirt PaaS Infrastructure
##################################################################################

depends = []

def safe_append(depends, resource):
    if resource:
        depends.append(resource)

##################################################################################
# Deploy Cilium
def run_cilium():
    if cilium_enabled:
        namespace = "kube-system"
        l2announcements = config_cilium.get('l2announcements') or "192.168.1.70/28"
        l2_bridge_name = config_cilium.get('l2_bridge_name') or "br0"
        cilium_version = config_cilium.get('version') # or "1.14.7"

        cilium = deploy_cilium(
            "cilium-cni",
            k8s_provider,
            kubernetes_distribution,
            project_name,
            kubernetes_endpoint_service_address,
            namespace,
            cilium_version,
            l2_bridge_name,
            l2announcements,
        )
        cilium_version = cilium[0]
        cilium_release = cilium[1]

        safe_append(depends, cilium_release)

        return cilium_version, cilium_release
    return None, None

cilium_version, cilium_release = run_cilium()

versions["cilium"] = {"enabled": cilium_enabled, "version": cilium_version}

##################################################################################
# Deploy Cert Manager
def run_cert_manager():
    if cert_manager_enabled:
        ns_name = "cert-manager"
        cert_manager_version = config_cert_manager.get('version') or None

        cert_manager = deploy_cert_manager(
            ns_name,
            cert_manager_version,
            kubernetes_distribution,
            depends,
            k8s_provider
        )

        versions["cert_manager"] = {"enabled": cert_manager_enabled, "version": cert_manager[0]}
        cert_manager_release = cert_manager[1]
        cert_manager_selfsigned_cert = cert_manager[2]

        pulumi.export("cert_manager_selfsigned_cert", cert_manager_selfsigned_cert)

        safe_append(depends, cert_manager_release)

        return cert_manager, cert_manager_release, cert_manager_selfsigned_cert
    return None, None, None

cert_manager, cert_manager_release, cert_manager_selfsigned_cert = run_cert_manager()

##################################################################################
# Deploy Prometheus
def run_prometheus():
    if prometheus_enabled:
        ns_name = "monitoring"
        prometheus_version = config_prometheus.get('version') or None

        prometheus = deploy_prometheus(
            depends,
            ns_name,
            prometheus_version,
            k8s_provider,
            openunison_enabled
        )

        versions["prometheus"] = {"enabled": prometheus_enabled, "version": prometheus[0]}
        prometheus_release = prometheus[1]

        safe_append(depends, prometheus_release)

        return prometheus, prometheus_release
    return None, None

prometheus, prometheus_release = run_prometheus()

##################################################################################
# Deploy Kubernetes Dashboard
def run_kubernetes_dashboard():
    if kubernetes_dashboard_enabled:
        ns_name = "kubernetes-dashboard"
        kubernetes_dashboard_version = config_kubernetes_dashboard.get('version') or None

        if cilium_enabled:
            safe_append(depends, cilium_release)

        kubernetes_dashboard = deploy_kubernetes_dashboard(
            depends,
            ns_name,
            kubernetes_dashboard_version,
            k8s_provider
        )

        versions["kubernetes_dashboard"] = {
            "enabled": kubernetes_dashboard_enabled,
            "version": kubernetes_dashboard[0]
        }

        kubernetes_dashboard_release = kubernetes_dashboard[1]

        safe_append(depends, kubernetes_dashboard_release)

        return kubernetes_dashboard, kubernetes_dashboard_release
    return None, None

kubernetes_dashboard, kubernetes_dashboard_release = run_kubernetes_dashboard()

##################################################################################
def run_openunison():
    if openunison_enabled:
        ns_name = "openunison"
        openunison_version = config_openunison.get('version') or None
        domain_suffix = config_openunison.get('dns_suffix') or "kargo.arpa"
        cluster_issuer = config_openunison.get('cluster_issuer') or "cluster-selfsigned-issuer-ca"

        config_openunison_github = config_openunison.get_object('github') or {}
        openunison_github_teams = config_openunison_github.get('teams')
        openunison_github_client_id = config_openunison_github.get('client_id')
        openunison_github_client_secret = config_openunison_github.get('client_secret')

        enabled = {}

        if prometheus_enabled:
            enabled["prometheus"] = {"enabled": prometheus_enabled}

        openunison = deploy_openunison(
            depends,
            ns_name,
            openunison_version,
            k8s_provider,
            domain_suffix,
            cluster_issuer,
            cert_manager_selfsigned_cert,
            kubernetes_dashboard_release,
            openunison_github_client_id,
            openunison_github_client_secret,
            openunison_github_teams,
            enabled,
        )

        versions["openunison"] = {"enabled": openunison_enabled, "version": openunison[0]}
        openunison_release = openunison[1]

        safe_append(depends, openunison_release)

        return openunison, openunison_release
    return None, None

openunison, openunison_release = run_openunison()

##################################################################################
# Deploy Ubuntu VM
def run_ubuntu_vm():
    if vm_enabled:

        # Get the SSH Public Key string from Pulumi Config if it exists
        # Otherwise, read the SSH Public Key from the local filesystem
        # TODO: Add user prompt before reading the SSH Public Key from the local filesystem
        ssh_pub_key = config.get("ssh_pub_key")
        if not ssh_pub_key:
            # Get the SSH public key
            with open(f"{os.environ['HOME']}/.ssh/id_rsa.pub", "r") as f:
                ssh_pub_key = f.read().strip()

        # Define the default values
        default_vm_config = {
            "namespace": "default",
            "instance_name": "ubuntu",
            "image_name": "docker.io/containercraft/ubuntu:22.04",
            "node_port": 30590,
            "ssh_user": "kc2",
            "ssh_password": "kc2",
            "ssh_pub_key": ssh_pub_key
        }

        # Merge the default values with the existing config_vm values
        config_vm_merged = {**default_vm_config, **{k: v for k, v in config_vm.items() if v is not None}}

        # Pass the merged configuration to the deploy_ubuntu_vm function
        ubuntu_vm, ubuntu_ssh_service = deploy_ubuntu_vm(
            config_vm_merged,
            k8s_provider,
            depends
        )

        versions["ubuntu_vm"] = {
            "enabled": vm_enabled,
            "name": ubuntu_vm.metadata["name"]
        }

        safe_append(depends, ubuntu_ssh_service)

        return ubuntu_vm, ubuntu_ssh_service

    return None, None

ubuntu_vm, ubuntu_ssh_service = run_ubuntu_vm()

# Export the component versions
pulumi.export("versions", versions)
