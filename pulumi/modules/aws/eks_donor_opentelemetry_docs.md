# AWS Distro for OpenTelemetry (ADOT) with Amazon EKS

## Overview

The **AWS Distro for OpenTelemetry (ADOT)** provides a secure, production-ready, AWS-supported distribution of the **OpenTelemetry** project. It enables the collection and export of telemetry data (metrics and traces) from your applications running on Amazon EKS to AWS services like Amazon Managed Service for Prometheus (AMP), Amazon CloudWatch, and AWS X-Ray.

By integrating ADOT with Amazon EKS, you can simplify the setup and management of observability pipelines, allowing you to gain deep insights into your applications and infrastructure with minimal overhead.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements and Prerequisites](#requirements-and-prerequisites)
3. [Installation](#installation)
   - [TLS Certificate Configuration](#tls-certificate-configuration)
   - [Installation via AWS Management Console](#installation-via-aws-management-console)
   - [Installation via AWS CLI](#installation-via-aws-cli)
4. [Collector Configuration](#collector-configuration)
   - [Deployment Modes](#deployment-modes)
   - [Example Collector Configurations](#example-collector-configurations)
   - [Advanced Configurations](#advanced-configurations)
5. [Advanced Configuration for Add-on Versions](#advanced-configuration-for-add-on-versions)
6. [Instrumenting Applications](#instrumenting-applications)
   - [Auto-Instrumentation Injection](#auto-instrumentation-injection)
   - [Configuring Auto-Instrumentation with Instrumentation CRD](#configuring-auto-instrumentation-with-instrumentation-crd)
7. [Kubernetes Attributes Processor](#kubernetes-attributes-processor)
8. [Target Allocator](#target-allocator)
9. [Monitoring and Verification](#monitoring-and-verification)
10. [Troubleshooting](#troubleshooting)
11. [Resources and Support](#resources-and-support)
12. [Stay Connected](#stay-connected)

---

## Introduction

The AWS Distro for OpenTelemetry (ADOT) simplifies the deployment and management of OpenTelemetry components in Amazon EKS. By using the ADOT Operator as an EKS add-on, you can streamline the installation, updates, and configurations of the OpenTelemetry Collector, enhancing observability without extensive manual setup.

### Key Components

- **ADOT Operator**: Manages the lifecycle of the OpenTelemetry Collector within the Kubernetes environment, using Custom Resource Definitions (CRDs).
- **ADOT Collector**: Receives, processes, and exports telemetry data for both metrics and traces to various AWS services.

An end-to-end pipeline in ADOT consists of multiple telemetry data flows, including:

- **Prometheus Metrics Collection**: Collects and sends Prometheus metrics to Amazon Managed Service for Prometheus (AMP).
- **Metrics Pipeline**: Receives OTLP metrics and forwards them to AMP and Amazon CloudWatch.
- **Tracing Pipeline**: Collects distributed traces and sends them to AWS X-Ray.

![ADOT Operator EKS Pipeline Diagram](#)

---

## Requirements and Prerequisites

Before installing ADOT on Amazon EKS, ensure that you have the following:

1. **Amazon EKS Cluster**: An EKS cluster running Kubernetes version 1.21 or higher.
   ```bash
   kubectl version | grep "Server Version"
   ```

2. **kubectl**: Installed and configured for your EKS cluster.
   ```bash
   aws eks update-kubeconfig --name <cluster_name> --region <your_aws_region>
   ```

3. **eksctl**: Installed for managing EKS clusters.

4. **AWS CLI v2**: Installed and configured.

5. **IAM Permissions**: Sufficient IAM roles and policies for EKS and ADOT.

6. **RBAC Permissions**: Required if installing an add-on version v0.62.1 or earlier.
   ```bash
   kubectl apply -f https://amazon-eks.s3.amazonaws.com/docs/addons-otel-permissions.yaml
   ```

**Note**: Currently, ADOT does not support Windows nodes or connected clusters in EKS.

---

## Installation

### TLS Certificate Configuration

The ADOT Operator uses admission webhooks to manage OpenTelemetry Collector configurations, which require a TLS certificate trusted by the Kubernetes API server. It is recommended to use **cert-manager** for managing TLS certificates.

#### Steps to Install cert-manager

1. **Install cert-manager**:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.8.2/cert-manager.yaml
   ```

2. **Verify cert-manager Deployment**:
   Check that the cert-manager pods are running in the `cert-manager` namespace.
   ```bash
   kubectl get pods -w -n cert-manager
   ```

   **Expected Output**:
   ```
   NAME                                       READY   STATUS    RESTARTS   AGE
   cert-manager-5597cff495-mnb2p              1/1     Running   0          12s
   cert-manager-cainjector-bd5f9c764-8jp5g    1/1     Running   0          12s
   cert-manager-webhook-5f57f59fbc-h9st8      1/1     Running   0          12s
   ```

For more details on certificate management, refer to the [cert-manager documentation](https://cert-manager.io/docs/).

### Installation via AWS Management Console

1. **Open Amazon EKS Console**:
   - Navigate to [Amazon EKS Console](https://console.aws.amazon.com/eks/home#/clusters).

2. **Select Cluster**:
   - In the left pane, choose **Clusters** and select your EKS cluster.

3. **Add ADOT Add-On**:
   - Go to the **Add-ons** tab and click **Get more add-ons**.
   - Under **Amazon EKS-addons**, select **AWS Distro for OpenTelemetry** and click **Next**.

4. **Configure Add-On Settings**:
   - Choose the desired **Version** for the ADOT add-on.
   - For custom configurations, expand **Optional configuration settings** and input relevant values for the ADOT Collector.

5. **Conflict Resolution**:
   - If the cluster already has a service account without an IAM role, select **Override** under **Conflict resolution method**.

6. **Review and Install**:
   - Verify settings on the **Review and add** page, then click **Create**.
   - After installation, ADOT will appear under installed add-ons.

### Installation via AWS CLI

1. **Enable ADOT Add-On for EKS**:
   ```bash
   aws eks create-addon --cluster-name <your-cluster-name> --addon-name adot
   ```

2. **Verify Add-On Installation**:
   - Confirm that the ADOT Operator is running in the `opentelemetry-operator-system` namespace.
     ```bash
     kubectl get pods -n opentelemetry-operator-system
     ```

   - Check the status of the add-on:
     ```bash
     aws eks describe-addon --addon-name adot --cluster-name <your-cluster-name>
     ```
     The `status` should be `"ACTIVE"`.

---

## Collector Configuration

The ADOT Collector can be deployed in various modes and configured to collect and export telemetry data according to your needs.

### Deployment Modes

- **Deployment**: Ideal for centralized metrics and trace collection.
- **DaemonSet**: Suitable for node-level monitoring.
- **StatefulSet**: Supports stateful workloads.
- **Sidecar**: Used when a sidecar pattern is preferred for application pods.

### Example Collector Configurations

#### 1. Combined Metrics and Traces Collector

This configuration collects Prometheus metrics and OTLP traces, exporting metrics to Amazon Managed Service for Prometheus and traces to AWS X-Ray.

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: sample-adot-collector
spec:
  mode: deployment
  config:
    receivers:
      prometheus:
        config:
          scrape_configs:
            - job_name: 'kubernetes-nodes'
              kubernetes_sd_configs:
                - role: node
      otlp:
        protocols:
          grpc:
          http:
    processors:
      batch:
    exporters:
      prometheusremotewrite:
        endpoint: "<AMP_REMOTE_WRITE_ENDPOINT>"
        auth:
          authenticator: sigv4auth
      awsxray:
    extensions:
      sigv4auth:
        region: "<AWS_REGION>"
        service: "aps"
    service:
      extensions: [sigv4auth]
      pipelines:
        metrics:
          receivers: [prometheus]
          processors: [batch]
          exporters: [prometheusremotewrite]
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [awsxray]
```

#### 2. CloudWatch Metrics Collector Configuration

Exports metrics to Amazon CloudWatch.

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: adot-collector-cloudwatch
spec:
  mode: deployment
  config:
    receivers:
      prometheus:
        config:
          scrape_configs:
            - job_name: 'cloudwatch-sample'
              static_configs:
                - targets: ['localhost:9090']
    processors:
      batch:
        timeout: 5s
    exporters:
      awsemf:
        region: "<AWS_REGION>"
    service:
      pipelines:
        metrics:
          receivers: [prometheus]
          processors: [batch]
          exporters: [awsemf]
```

#### 3. X-Ray Traces Collector Configuration

Exports traces to AWS X-Ray.

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: adot-collector-xray
spec:
  mode: deployment
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:55680
    processors:
      batch:
        timeout: 5s
    exporters:
      awsxray:
        region: "<AWS_REGION>"
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [awsxray]
```

### Advanced Configurations

For complex observability needs, you can combine multiple receivers, processors, and exporters in a single ADOT Collector configuration.

Examples include:

- **Combining Prometheus and OTLP Receivers**: Collect both metrics and traces from your applications.
- **Multiple Exporters**: Send metrics to both Amazon Managed Prometheus and CloudWatch simultaneously.

---

## Advanced Configuration for Add-on Versions

### For Versions Pre-v0.88.0-eksbuild.1

For versions before `v0.88.0-eksbuild.1`, configurations are provided as a JSON string using the `--configuration-values` option during add-on creation or update.

#### Example: Setting CPU Limits and Replica Count

```json
{
  "manager": {
    "resources": {
      "limits": {
        "cpu": "200m"
      }
    }
  },
  "replicaCount": 2
}
```

#### Applying the Configuration

```bash
aws eks create-addon \
    --cluster-name <YOUR-EKS-CLUSTER-NAME> \
    --addon-name adot \
    --configuration-values file://configuration-values.json \
    --resolve-conflicts OVERWRITE
```

### For Versions v0.88.0 and Above

For `v0.88.0` and newer versions:

- Use the `OpenTelemetryCollector` CRD to specify configurations.
- Enhanced customization options are available.
- Follow the AWS-provided migration guide when upgrading from earlier versions.

---

## Instrumenting Applications

### Auto-Instrumentation Injection

ADOT supports **auto-instrumentation injection** for applications running on Amazon EKS, enabling automatic injection of OpenTelemetry libraries into workloads without modifying application code.

#### Enabling Auto-Instrumentation

Annotate your workloads:

```yaml
instrumentation.opentelemetry.io/inject-<language>: "true"
```

**Supported Languages**:

- **Java**
- **Node.js**
- **Python**
- **.NET**

#### Example: Java Application

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-java-app
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: my-java-app
      annotations:
        instrumentation.opentelemetry.io/inject-java: "true"
    spec:
      containers:
        - name: app-container
          image: my-java-app-image
```

### Configuring Auto-Instrumentation with Instrumentation CRD

Use the **Instrumentation CRD** to customize auto-instrumentation settings.

#### Example Configuration

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: my-instrumentation
spec:
  exporter:
    endpoint: http://adot-collector:4317
  java:
    image: public.ecr.aws/aws-observability/adot-autoinstrumentation-java:v1.31.1
```

---

## Kubernetes Attributes Processor

The **Kubernetes Attributes Processor** enriches telemetry signals with Kubernetes metadata, enhancing observability by providing context for signals received from various Kubernetes resources.

### Configuration Example

```yaml
processors:
  k8sattributes:
    pod_association:
      - sources:
          - from: connection
```

Integrate the processor into your pipelines to automatically attach Kubernetes resource attributes like `k8s.pod.name`, `k8s.namespace.name`, and `k8s.node.name` to your telemetry data.

---

## Target Allocator

The **Target Allocator (TA)** enables flexible and scalable Prometheus service discovery and metrics collection by decoupling scrape target discovery from metrics collection.

### Enabling the Target Allocator

Set `OpenTelemetryCollector.spec.targetAllocator.enabled` to `true` in the OpenTelemetry Collector CRD.

#### Example Configuration

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: collector-with-ta
spec:
  mode: statefulset
  targetAllocator:
    enabled: true
  config: |
    receivers:
      prometheus:
        config:
          scrape_configs:
            - job_name: 'otel-collector'
              scrape_interval: 10s
              static_configs:
                - targets: ['0.0.0.0:8888']
    processors:
      batch:
    exporters:
      prometheusremotewrite:
        endpoint: "<AMP_REMOTE_WRITE_ENDPOINT>"
        auth:
          authenticator: sigv4auth
    extensions:
      sigv4auth:
        region: "<AWS_REGION>"
        service: "aps"
    service:
      pipelines:
        metrics:
          receivers: [prometheus]
          processors: [batch]
          exporters: [prometheusremotewrite]
```

---

## Monitoring and Verification

After deploying ADOT, monitor and verify your setup:

1. **Verify Collector Logs**:
   ```bash
   kubectl logs <collector-pod-name> -n opentelemetry-operator-system
   ```

2. **Access Metrics in Amazon Managed Prometheus or CloudWatch**:
   - Ensure metrics are being collected and exported as configured.

3. **View Traces in AWS X-Ray**:
   - Validate that traces from your applications are visible in AWS X-Ray.

---

## Troubleshooting

### Common Errors

1. **Access Denied for `eks:addon-manager` Role**:
   - **Error Message**: `"roles.rbac.authorization.k8s.io "opentelemetry-operator-leader-election-role" is forbidden"`
   - **Solution**: Update IAM permissions for the `eks:addon-manager` role in the `opentelemetry-operator-system` namespace.

2. **CREATE_FAILED or UPDATE_FAILED**:
   - **Cause**: Conflict or unsupported architecture.
   - **Solution**: Use `--resolve-conflicts OVERWRITE` in the EKS command or ensure architecture compatibility for your add-on version.

3. **DELETE_FAILED**:
   - **Cause**: EKS management conflicts.
   - **Solution**: Add the `--preserve` flag when deleting the add-on:
     ```bash
     aws eks delete-addon --cluster-name <your-cluster-name> --addon-name adot --preserve
     ```

---

## Resources and Support

For further reading and support, refer to:

- **AWS Distro for OpenTelemetry Documentation**: [aws-otel.github.io](https://aws-otel.github.io/)
- **GitHub Repository**: [aws-observability/aws-otel-collector](https://github.com/aws-observability/aws-otel-collector)
- **OpenTelemetry Specification**: [opentelemetry.io](https://opentelemetry.io/)
- **cert-manager Documentation**: [cert-manager.io/docs](https://cert-manager.io/docs/)

---

## Stay Connected

- **GitHub Community**: [AWS Observability on GitHub](https://github.com/aws-observability)
- **Twitter**: Follow [@AWSOpenSource](https://twitter.com/AWSOpenSource) for updates on ADOT and other AWS observability tools.

For issues or enhancement requests, file an issue on the [GitHub repository](https://github.com/aws-observability/aws-otel-collector/issues).
