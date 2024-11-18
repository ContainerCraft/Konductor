# AWS Distro for OpenTelemetry (ADOT) Integration Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Implementation Guide](#implementation-guide)
5. [Configuration Management](#configuration-management)
6. [Deployment Steps](#deployment-steps)
7. [Validation and Testing](#validation-and-testing)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Future Enhancements](#future-enhancements)
11. [References](#references)

## Introduction

This guide provides comprehensive documentation for integrating AWS Distro for OpenTelemetry (ADOT) with Amazon EKS clusters in the Konductor platform. ADOT provides a secure, production-ready distribution of the OpenTelemetry project, enabling the collection and export of telemetry data from applications running on Amazon EKS.

### Purpose

- Enable comprehensive observability for EKS workloads
- Implement standardized telemetry collection
- Support multiple monitoring backends
- Ensure compliance with observability requirements

### Scope

This document covers:
- ADOT Operator installation and configuration
- Collector setup and customization
- Application instrumentation
- Integration with AWS services
- Monitoring and troubleshooting

## Prerequisites

- Existing EKS cluster (1.21+)
- Helm 3.x
- kubectl configured for cluster access
- AWS CLI with appropriate permissions
- cert-manager installed (for TLS certificate management)

### Required Permissions

```python
class AdotIamConfig(TypedDict):
    """IAM configuration for ADOT deployment.

    Attributes:
        role_name: Name of the IAM role
        namespace: Kubernetes namespace
        service_account: Service account name
    """
    role_name: str
    namespace: str
    service_account: str

adot_iam_defaults: AdotIamConfig = {
    "role_name": "adot-collector",
    "namespace": "adot-system",
    "service_account": "adot-collector"
}
```

## Architecture Overview

### Components

1. **ADOT Operator**
   - Manages collector lifecycle
   - Handles configuration updates
   - Ensures high availability

2. **Collector**
   - Receives telemetry data
   - Processes and transforms data
   - Exports to destinations

3. **Instrumentation**
   - Auto-instrumentation injection
   - Manual instrumentation support
   - Custom instrumentation options

### Integration Points

```python
class AdotCollectorConfig(TypedDict):
    """ADOT Collector configuration structure.

    Attributes:
        mode: Deployment mode (sidecar, daemon, deployment)
        replicas: Number of collector replicas
        resources: Resource requirements
        config: Collector configuration
    """
    mode: str
    replicas: int
    resources: Dict[str, Any]
    config: Dict[str, Any]
```

## Implementation Guide

### ADOT Operator Installation

1. **Create Namespace**

```python
def create_adot_namespace(
    name: str = "adot-system",
    labels: Optional[Dict[str, str]] = None
) -> k8s.core.v1.Namespace:
    """Create namespace for ADOT components."""
    if not labels:
        labels = {"name": name}

    return k8s.core.v1.Namespace(
        name,
        metadata={
            "name": name,
            "labels": labels
        }
    )
```

2. **Deploy Operator**

```python
def deploy_adot_operator(
    config: AdotOperatorConfig,
    namespace: str
) -> k8s.helm.v3.Release:
    """Deploy ADOT Operator using Helm."""
    return k8s.helm.v3.Release(
        "adot-operator",
        chart="adot-operator",
        namespace=namespace,
        repository="https://aws.github.io/eks-charts",
        version=config["version"],
        values=config["values"]
    )
```

### Collector Configuration

Example collector configuration:

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: adot-collector
spec:
  mode: deployment
  serviceAccount: adot-collector
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024

    exporters:
      awsxray:
        region: ${AWS_REGION}
      awsemf:
        region: ${AWS_REGION}
        log_group_name: "/aws/containerinsights/${CLUSTER_NAME}/performance"
        log_stream_name: "${HOST_NAME}"

    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [awsxray]
        metrics:
          receivers: [otlp]
          processors: [batch]
          exporters: [awsemf]
```

### Implementation in Pulumi

```python
def deploy_adot_collector(
    config: AdotCollectorConfig,
    namespace: str,
    depends_on: List[pulumi.Resource] = None
) -> pulumi.CustomResource:
    """Deploy ADOT Collector with configuration."""
    return k8s.apiextensions.CustomResource(
        "adot-collector",
        api_version="opentelemetry.io/v1alpha1",
        kind="OpenTelemetryCollector",
        metadata={
            "name": "adot-collector",
            "namespace": namespace
        },
        spec={
            "mode": config["mode"],
            "serviceAccount": config["service_account"],
            "config": config["collector_config"]
        },
        opts=pulumi.ResourceOptions(depends_on=depends_on)
    )
```

## Configuration Management

### TypedDict Configurations

```python
class AdotConfig(TypedDict):
    """Main ADOT configuration structure."""
    operator: AdotOperatorConfig
    collector: AdotCollectorConfig
    iam: AdotIamConfig

# Default configuration
adot_defaults: AdotConfig = {
    "operator": {
        "version": "v0.24.0",
        "values": {
            "serviceAccount": {
                "create": True,
                "annotations": {}
            }
        }
    },
    "collector": {
        "mode": "deployment",
        "replicas": 2,
        "resources": {
            "limits": {
                "cpu": "1",
                "memory": "2Gi"
            },
            "requests": {
                "cpu": "200m",
                "memory": "400Mi"
            }
        }
    },
    "iam": adot_iam_defaults
}
```

## Deployment Steps

1. **Prepare Environment**
   - Create namespace
   - Configure IAM roles
   - Set up service accounts

2. **Deploy Components**
   - Install ADOT Operator
   - Deploy Collector
   - Configure auto-instrumentation

3. **Validate Installation**
   - Check component status
   - Verify telemetry flow
   - Test instrumentation

## Validation and Testing

### Health Checks

```python
def validate_adot_deployment(
    namespace: str
) -> bool:
    """Validate ADOT deployment status."""
    try:
        # Check operator status
        operator_status = k8s.core.v1.list_namespaced_pod(
            namespace,
            label_selector="app=adot-operator"
        )

        # Check collector status
        collector_status = k8s.core.v1.list_namespaced_pod(
            namespace,
            label_selector="app=adot-collector"
        )

        return all([
            operator_status.items[0].status.phase == "Running",
            collector_status.items[0].status.phase == "Running"
        ])
    except Exception as e:
        log.error(f"Validation failed: {str(e)}")
        return False
```

## Troubleshooting

### Common Issues

1. **Collector Not Starting**
   - Check IAM roles and permissions
   - Verify resource requirements
   - Review collector configuration

2. **Data Not Flowing**
   - Validate endpoint configuration
   - Check network policies
   - Review exporter settings

### Logging

```python
def configure_adot_logging(
    namespace: str,
    log_level: str = "info"
) -> None:
    """Configure ADOT component logging."""
    k8s.core.v1.ConfigMap(
        "adot-logging",
        metadata={"namespace": namespace},
        data={
            "collector.yaml": f"""
            logging:
              level: {log_level}
              development: false
              encoding: json
            """
        }
    )
```

## Best Practices

1. **Resource Management**
   - Size collectors appropriately
   - Use horizontal scaling
   - Implement resource limits

2. **Security**
   - Enable TLS encryption
   - Use service accounts
   - Implement network policies

3. **Monitoring**
   - Monitor collector health
   - Track telemetry pipeline
   - Set up alerts

## Future Enhancements

### Planned Features

1. **Advanced Configuration**
   - Custom processors
   - Additional exporters
   - Enhanced filtering

2. **Integration Improvements**
   - Additional AWS services
   - Third-party systems
   - Custom instrumentation

### Roadmap Items

1. **Short-term**
   - Performance optimization
   - Enhanced auto-instrumentation
   - Additional metric support

2. **Long-term**
   - Multi-cluster support
   - Advanced sampling
   - Custom processors

## References

- [AWS Distro for OpenTelemetry Documentation](https://aws-otel.github.io/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [AWS X-Ray Documentation](https://docs.aws.amazon.com/xray/latest/devguide/aws-xray.html)
- [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html)

---

**Note**: This document is actively maintained. For updates and changes, refer to the [changelog](./changelog.md).
