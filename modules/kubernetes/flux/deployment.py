# modules/kubernetes/flux/deployment.py
from typing import Dict, Any, List
from pulumi import log, ResourceOptions, CustomTimeouts
import pulumi_kubernetes as k8s

from ..deployment import KubernetesModule
from .types import FluxConfig
from modules.core.interfaces import ModuleDeploymentResult


class FluxModule(KubernetesModule):
    """Flux module implementation."""

    def __init__(self, init_config):
        super().__init__(init_config)
        self.name = "flux"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Flux configuration."""
        try:
            if config is None:
                config = {}
            FluxConfig(**config)
            return []
        except Exception as e:
            return [str(e)]

    def deploy(self, config: Dict[str, Any]) -> ModuleDeploymentResult:
        """Deploy Flux system."""
        try:
            # Parse config
            flux_config = FluxConfig(**config)

            # Deploy namespace
            namespace = k8s.core.v1.Namespace(
                f"{self.name}-namespace",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=flux_config.namespace,
                    labels=flux_config.labels,
                    annotations=flux_config.annotations,
                ),
                opts=ResourceOptions(provider=self.provider.provider)
            )

            # Deploy Flux components using Helm
            chart_name = "flux2"
            chart_url = "https://fluxcd-community.github.io/helm-charts"

            # Configure Helm values
            helm_values = {
                "git": {
                    "url": flux_config.git_repository,
                    "branch": flux_config.git_branch,
                    "path": flux_config.git_path,
                },
                "interval": flux_config.interval,
                "components": {
                    component: {"enabled": component in flux_config.components}
                    for component in [
                        "source-controller",
                        "kustomize-controller",
                        "helm-controller",
                        "notification-controller",
                    ]
                },
            }

            # Deploy Helm release
            release = k8s.helm.v3.Release(
                f"{self.name}-system",
                k8s.helm.v3.ReleaseArgs(
                    chart=chart_name,
                    version=flux_config.version,
                    namespace=flux_config.namespace,
                    repository_opts=k8s.helm.v3.RepositoryOptsArgs(repo=chart_url),
                    values=helm_values,
                ),
                opts=ResourceOptions(
                    provider=self.provider.provider,
                    parent=namespace,
                    depends_on=[namespace],
                    custom_timeouts=CustomTimeouts(
                        create="2m",
                        update="2m",
                        delete="2m"
                    ),
                ),
            )

            # TODO: Uncomment this when we have a git repository
            ## Create GitRepository resource
            #git_repo = k8s.apiextensions.CustomResource(
            #    f"{self.name}-gitrepository",
            #    api_version="source.toolkit.fluxcd.io/v1",
            #    kind="GitRepository",
            #    metadata=k8s.meta.v1.ObjectMetaArgs(
            #        name="flux-system",
            #        namespace=flux_config.namespace,
            #    ),
            #    spec={
            #        "interval": flux_config.interval,
            #        "ref": {
            #            "branch": flux_config.git_branch,
            #        },
            #        "url": flux_config.git_repository,
            #    },
            #    opts=ResourceOptions(provider=self.provider.provider, parent=release, depends_on=[release]),
            #)

            ## Create Kustomization resource
            #kustomization = k8s.apiextensions.CustomResource(
            #    f"{self.name}-kustomization",
            #    api_version="kustomize.toolkit.fluxcd.io/v1",
            #    kind="Kustomization",
            #    metadata=k8s.meta.v1.ObjectMetaArgs(
            #        name="flux-system",
            #        namespace=flux_config.namespace,
            #    ),
            #    spec={
            #        "interval": flux_config.interval,
            #        "path": flux_config.git_path,
            #        "prune": True,
            #        "sourceRef": {
            #            "kind": "GitRepository",
            #            "name": "flux-system",
            #        },
            #    },
            #    opts=ResourceOptions(provider=self.provider.provider, parent=git_repo, depends_on=[git_repo]),
            #)

            # Return deployment result
            resource_ids = [
                f"{self.name}-namespace",
                f"{self.name}-system",
                f"{self.name}-gitrepository",
                f"{self.name}-kustomization",
            ]

            return ModuleDeploymentResult(
                success=True,
                version=flux_config.version or "latest",
                resources=resource_ids,
                metadata={
                    "namespace": flux_config.namespace,
                    "git_repository": flux_config.git_repository,
                    "git_branch": flux_config.git_branch,
                    "components": flux_config.components,
                },
            )

        except Exception as e:
            log.error(f"Failed to deploy Flux: {str(e)}")
            return ModuleDeploymentResult(success=False, version="", errors=[str(e)])
