# src/core/config/schemas/core_schema.py

"""Core schema definition for configuration validation.

This module defines the JSON schema for validating the core configuration
structure, including project settings, logging configuration, and provider
enablement status.
"""

# JSON Schema Draft 7 for validating the core configuration
SCHEMA_DEFINITION = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Core Configuration Schema",
    "description": "Schema for validating core module configuration",
    "type": "object",
    "properties": {
        "project": {
            "type": "object",
            "description": "Project-related configuration",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the project"
                },
                "environment": {
                    "type": "string",
                    "description": "Deployment environment",
                    "enum": ["dev", "test", "stage", "prod", "production"]
                },
                "organization": {
                    "type": "string",
                    "description": "Organization name"
                }
            },
            "required": ["name", "environment"]
        },
        "logging": {
            "type": "object",
            "description": "Logging configuration",
            "properties": {
                "level": {
                    "type": "string",
                    "description": "Logging level",
                    "enum": ["debug", "info", "warning", "error", "critical"]
                },
                "format": {
                    "type": "string",
                    "description": "Log output format",
                    "enum": ["text", "json"]
                },
                "console": {
                    "type": "boolean",
                    "description": "Whether to log to console"
                }
            },
            "required": ["level"]
        },
        "providers": {
            "type": "object",
            "description": "Global provider configuration",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Global switch to enable/disable all providers"
                }
            }
        },
        "aws": {
            "type": "object",
            "description": "AWS provider configuration",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable AWS provider"
                },
                "region": {
                    "type": "string",
                    "description": "Default AWS region"
                },
                "instances": {
                    "type": "object",
                    "description": "Named provider instances",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "region": {
                                "type": "string",
                                "description": "AWS region for this provider"
                            }
                        },
                        "required": ["region"]
                    }
                }
            },
            "required": ["enabled"]
        },
        "azure": {
            "type": "object",
            "description": "Azure provider configuration",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable Azure provider"
                },
                "location": {
                    "type": "string",
                    "description": "Default Azure location"
                },
                "instances": {
                    "type": "object",
                    "description": "Named provider instances",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Azure location for this provider"
                            },
                            "subscription_id": {
                                "type": "string",
                                "description": "Azure subscription ID"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            "required": ["enabled"]
        },
        "kubernetes": {
            "type": "object",
            "description": "Kubernetes provider configuration",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable Kubernetes provider"
                },
                "context": {
                    "type": "string",
                    "description": "Default Kubernetes context"
                },
                "instances": {
                    "type": "object",
                    "description": "Named provider instances",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "string",
                                "description": "Kubernetes context for this provider"
                            },
                            "kubeconfig_path": {
                                "type": "string",
                                "description": "Path to kubeconfig file"
                            }
                        },
                        "required": ["context"]
                    }
                }
            },
            "required": ["enabled"]
        }
    },
    "required": ["project", "providers"]
}
