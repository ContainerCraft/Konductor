# pulumi/core/types.py

"""
Types and Data Structures Module

This module defines all shared data classes and types used across all modules.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator


class NamespaceConfig(BaseModel):
    name: str
    labels: Dict[str, str] = {"ccio.v1/app": "kargo"}
    annotations: Dict[str, str] = {}
    finalizers: List[str] = ["kubernetes"]
    protect: bool = False
    retain_on_delete: bool = False
    ignore_changes: List[str] = ["metadata", "spec"]
    custom_timeouts: Dict[str, str] = {"create": "5m", "update": "10m", "delete": "10m"}


class FismaConfig(BaseModel):
    enabled: bool = False
    level: Optional[str] = None
    ato: Dict[str, str] = {}

    @validator("enabled", pre=True)
    def parse_enabled(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class NistConfig(BaseModel):
    enabled: bool = False
    controls: List[str] = []
    auxiliary: List[str] = []
    exceptions: List[str] = []

    @validator("enabled", pre=True)
    def parse_enabled(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return bool(v)


class ScipConfig(BaseModel):
    environment: Optional[str] = None
    ownership: Dict[str, Any] = {}
    provider: Dict[str, Any] = {}


class ComplianceConfig(BaseModel):
    fisma: FismaConfig = FismaConfig()
    nist: NistConfig = NistConfig()
    scip: ScipConfig = ScipConfig()

    @classmethod
    def merge(cls, user_config: Dict[str, Any]) -> "ComplianceConfig":
        fisma_config = FismaConfig(**user_config.get("fisma", {}))
        nist_config = NistConfig(**user_config.get("nist", {}))
        scip_config = ScipConfig(**user_config.get("scip", {}))
        return cls(fisma=fisma_config, nist=nist_config, scip=scip_config)
