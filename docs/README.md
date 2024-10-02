# Konductor DevOps Template

# Introduction

# Fundamentals

# Getting Started

## Prerequisites

## Fork

## Run

## Try It

```bash
# Load environment variables, config files, and credentials
eval $(pulumi env open --format=shell containercraft/NavtecaAwsCredentialsConfigSmce/navteca-aws-credentials-config-smce)
```

```bash
# Test AWS CLi
aws sts get-caller-identity
```

```bash
# Create a new Pulumi Deployment Stack
pulumi stack select --create containercraft/konductor/navteca-aws-credentials-config-smce
```

## Cleanup

# Next Steps

# Resources
