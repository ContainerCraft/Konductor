# src/core/__init__.py

"""Core module for IaC framework.

This module contains the central functionality for the IaC framework,
including configuration management, provider registry, metadata management,
and deployment orchestration.
"""

from .module import CoreModule

__all__ = ["CoreModule"]
