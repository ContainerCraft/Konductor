# ./modules/core/compliance_types.py
"""
Compliance configuration types
"""
from pulumi import log, Config
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator


class FismaAto(BaseModel):
    """FISMA ATO configuration"""

    id: Optional[str] = Field(None, description="ATO identifier")
    authorized: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    eol: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_touch: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_config(cls, ato_config: Dict[str, Any], program_start_time: datetime) -> "FismaAto":
        """Create FismaAto from config dictionary"""
        if not ato_config:
            return cls(authorized=program_start_time, eol=program_start_time, last_touch=program_start_time)

        return cls(
            id=ato_config.get("id"),
            authorized=cls.parse_datetime(ato_config.get("authorized", program_start_time)),
            eol=cls.parse_datetime(ato_config.get("eol", program_start_time)),
            last_touch=program_start_time,
        )

    @validator("authorized", "eol", pre=True)
    def parse_datetime(cls, v):
        """Parse datetime strings into datetime objects"""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # First try parsing ISO format
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                except ValueError:
                    pass

                # Then try explicit formats
                formats = [
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%d %H:%M:%S %z",
                    "%Y-%m-%d %H:%M:%S +0000 UTC",
                    "%Y-%m-%d",
                ]

                for fmt in formats:
                    try:
                        dt = datetime.strptime(v, fmt)
                        return dt.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                raise ValueError(f"Could not parse datetime from {v}")

            except Exception as e:
                log.error(f"Failed to parse datetime '{v}': {str(e)}")
                raise ValueError(f"Invalid datetime format: {v}")
        raise ValueError(f"Invalid datetime value: {v}")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


@dataclass
class Fisma:
    ato: FismaAto = field(default_factory=FismaAto)
    enabled: bool = False
    level: str = "low"
    mode: str = "strict"


@dataclass
class Nist:
    auxiliary: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    enabled: bool = False
    exceptions: List[str] = field(default_factory=list)


@dataclass
class ScipOwnership:
    contacts: List[str] = field(default_factory=list)
    name: str = ""


@dataclass
class ScipProvider:
    name: str = ""
    regions: List[str] = field(default_factory=list)


@dataclass
class Scip:
    environment: str = "dev"
    ownership: Dict[str, ScipOwnership] = field(
        default_factory=lambda: {
            "operator": ScipOwnership(),
            "provider": ScipOwnership(),
        }
    )
    provider: ScipProvider = field(default_factory=ScipProvider)


class ComplianceConfig(BaseModel):
    """Compliance configuration with defaults"""

    fisma: Fisma = Field(default_factory=Fisma)
    nist: Nist = Field(default_factory=Nist)
    scip: Scip = Field(default_factory=Scip)

    @classmethod
    def from_pulumi_config(cls, config: Config, program_start_time: datetime) -> "ComplianceConfig":
        """Create ComplianceConfig from Pulumi stack configuration"""
        try:
            # Get compliance config from stack
            compliance_config = config.get_object("compliance") or {}

            # Get FISMA config
            fisma_config = compliance_config.get("fisma", {})
            ato_config = fisma_config.get("ato", {})

            # Create ATO instance
            ato = FismaAto(
                id=ato_config.get("id"),
                authorized=ato_config.get("authorized", program_start_time),
                eol=ato_config.get("eol", program_start_time),
                last_touch=program_start_time,
            )

            # Create and return complete config
            return cls(
                fisma=Fisma(
                    ato=ato,
                    enabled=fisma_config.get("enabled", False),
                    level=fisma_config.get("level", "low"),
                    mode=fisma_config.get("mode", "strict"),
                ),
                nist=Nist(**compliance_config.get("nist", {})),
                scip=Scip(**compliance_config.get("scip", {})),
            )
        except Exception as e:
            log.error(f"Error creating compliance config: {str(e)}")
            # Return default config instead of raising
            return cls()

    def to_dict(self) -> Dict[str, Any]:
        """Convert compliance metadata to dictionary format"""
        return {
            "fisma": {
                "ato": {
                    "id": self.fisma.ato.id,
                    "authorized": self.fisma.ato.authorized.isoformat() if self.fisma.ato.authorized else None,
                    "eol": self.fisma.ato.eol.isoformat() if self.fisma.ato.eol else None,
                    "last_touch": self.fisma.ato.last_touch.isoformat() if self.fisma.ato.last_touch else None,
                },
                "enabled": self.fisma.enabled,
                "level": self.fisma.level,
                "mode": self.fisma.mode,
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
                    "operator": {
                        "contacts": self.scip.ownership["operator"].contacts,
                        "name": self.scip.ownership["operator"].name,
                    },
                    "provider": {
                        "contacts": self.scip.ownership["provider"].contacts,
                        "name": self.scip.ownership["provider"].name,
                    },
                },
                "provider": {
                    "name": self.scip.provider.name,
                    "regions": self.scip.provider.regions,
                },
            },
        }

    class Config:
        arbitrary_types_allowed = True
