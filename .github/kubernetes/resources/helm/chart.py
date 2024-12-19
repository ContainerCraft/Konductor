# ./modules/kubernetes/resources/helm/chart.py
from typing import Dict, Any, Optional
from pulumi import ResourceOptions, CustomTimeouts
from pulumi_kubernetes.helm.v4 import Chart, RepositoryOptsArgs


def create_helm_chart(
    name: str,
    chart: str,
    namespace: str,
    version: str,
    values: Dict[str, Any],
    provider: Any,
    repository: Optional[str] = None,
    skip_await: bool = False,
    timeout: Optional[int] = 600,
    cleanup_on_fail: bool = True,
    atomic: bool = True,
    repository_opts: Optional[RepositoryOptsArgs] = None,
    opts: Optional[ResourceOptions] = None,
) -> Chart:
    """Deploy a Helm chart with enhanced configuration."""

    chart_args = {
        "chart": chart,
        "version": version,
        "namespace": namespace,
        "values": values,
        "skip_await": skip_await,
        "cleanup_on_fail": cleanup_on_fail,
        "atomic": atomic,
        "timeout": timeout,
    }

    if repository:
        chart_args["repo"] = repository

    if repository_opts:
        chart_args["repository_opts"] = repository_opts

    return Chart(
        name,
        chart_args,
        opts=opts or ResourceOptions(
            provider=provider,
            custom_timeouts=CustomTimeouts(
                create="20m",
                update="10m",
                delete="10m"
            ),
        ),
    )
