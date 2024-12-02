# ./modules/core/compliance_types.py
"""
Compliance configuration types
"""
from pulumi import log
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


@dataclass
class FismaAto:
    authorized: datetime
    renew: datetime
    review: datetime


@dataclass
class Fisma:
    ato: FismaAto
    enabled: bool = False
    level: str = "low"


@dataclass
class Nist:
    auxiliary: List[str] = Field(default_factory=list)
    controls: List[str] = Field(default_factory=list)
    enabled: bool = False
    exceptions: List[str] = Field(default_factory=list)


@dataclass
class ScipOwnership:
    contacts: List[str] = Field(default_factory=list)
    name: str = ""


@dataclass
class ScipProvider:
    name: str = ""
    regions: List[str] = Field(default_factory=list)


@dataclass
class Scip:
    environment: str = "dev"
    ownership: Dict[str, ScipOwnership] = Field(
        default_factory=lambda: {
            "operator": ScipOwnership(),
            "provider": ScipOwnership(),
        }
    )
    provider: ScipProvider = Field(default_factory=ScipProvider)


class ComplianceConfig(BaseModel):
    """Compliance configuration with defaults"""

    fisma: Fisma = Field(
        default_factory=lambda: Fisma(
            ato=FismaAto(
                authorized=datetime.now(), renew=datetime.now(), review=datetime.now()
            )
        )
    )
    nist: Nist = Field(default_factory=Nist)
    scip: Scip = Field(default_factory=Scip)

    @staticmethod
    def merge(user_config: Dict[str, Any]) -> "ComplianceConfig":
        """Merge user configuration with defaults"""
        default_config = ComplianceConfig()

        try:
            for key, value in user_config.items():
                if hasattr(default_config, key):
                    setattr(default_config, key, value)
                else:
                    log.warn(f"Unknown compliance configuration key: {key}")
        except Exception as e:
            log.warn(f"Error merging compliance config: {str(e)}")

        return default_config

    def to_dict(self) -> Dict[str, Any]:
        """Convert compliance metadata to dictionary format"""
        return {
            "fisma": {
                "ato": {
                    "authorized": self.fisma.ato.authorized.isoformat(),
                    "renew": self.fisma.ato.renew.isoformat(),
                    "review": self.fisma.ato.review.isoformat(),
                },
                "enabled": self.fisma.enabled,
                "level": self.fisma.level,
            },
            "nist": {
                "auxiliary": self.nist.auxiliary,
                "controls": self.nist.controls,
                "enabled": self.nist.enabled,
                "exceptions": self.nist.exceptions,
            },
            "scip": {
                "environment": self.scip.environment,
                "ownership": {
                    "operator": vars(self.scip.ownership["operator"]),
                    "provider": vars(self.scip.ownership["provider"]),
                },
                "provider": {
                    "name": self.scip.provider.name,
                    "regions": self.scip.provider.regions,
                },
            },
        }
