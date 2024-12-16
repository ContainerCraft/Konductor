# ./modules/core/types/compliance.py
"""
Core module compliance types implementation.
"""

from typing import List, Dict, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
import pulumi
from pulumi import log


class OwnershipInfo(TypedDict):
    """Owner contact information."""
    name: str
    contacts: List[str]


class AtoConfig(TypedDict):
    """ATO (Authority to Operate) configuration."""
    id: str
    authorized: str  # ISO datetime
    eol: str        # ISO datetime
    last_touch: str # ISO datetime


class ProjectOwnership(TypedDict):
    """Project ownership structure."""
    owner: OwnershipInfo
    operations: OwnershipInfo


class ProjectProviders(TypedDict):
    """Cloud provider configuration."""
    name: List[str]
    regions: List[str]


class ScipConfig(BaseModel):
    """SCIP project configuration."""
    environment: str = Field(..., description="e.g., prod-us-west")
    production: bool = Field(default=False)
    ownership: ProjectOwnership
    ato: AtoConfig
    providers: ProjectProviders


class FismaConfig(BaseModel):
    """FISMA compliance configuration."""
    level: str = Field(default="moderate")
    mode: str = Field(default="warn")


class NistConfig(BaseModel):
    """NIST compliance configuration."""
    auxiliary: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)


class ComplianceConfig(BaseModel):
    """
    Consolidated compliance configuration.

    Maps to the 'compliance' section of stack outputs.
    """
    project: ScipConfig
    fisma: FismaConfig
    nist: NistConfig

    @classmethod
    def from_pulumi_config(cls, config: pulumi.Config, timestamp: datetime) -> "ComplianceConfig":
        """
        Create ComplianceConfig from Pulumi config.

        Args:
            config: Pulumi configuration object
            timestamp: Current timestamp for configuration creation

        Returns:
            ComplianceConfig: Configuration instance
        """
        try:
            # Get compliance config from Pulumi config
            compliance_data = config.get_object("compliance") or {}

            # Get project config or initialize default
            project_data = compliance_data.get("project", {})

            # Determine if this is a production deployment
            is_production = project_data.get("production", False)

            # Handle ATO dates
            ato_data = project_data.get("ato", {})
            current_time = timestamp.isoformat()

            if is_production:
                # Production environments must have authorized date in config
                if "authorized" not in ato_data:
                    raise ValueError("Production environments require 'authorized' date in ATO configuration")
                authorized_date = ato_data["authorized"]
            else:
                # Non-production uses current timestamp
                authorized_date = current_time

            # Set EOL date
            if "eol" in ato_data:
                # Use configured EOL if provided
                eol_date = ato_data["eol"]
            else:
                if is_production:
                    # Production should have explicit EOL
                    raise ValueError("Production environments require 'eol' date in ATO configuration")
                else:
                    # Dev/non-prod gets 24h EOL from last_touch
                    eol_date = (timestamp + timedelta(hours=24)).isoformat()

            # Ensure required nested structures exist
            if "project" not in compliance_data:
                compliance_data["project"] = {
                    "environment": "dev",
                    "production": False,
                    "ownership": {
                        "owner": {"name": "default", "contacts": []},
                        "operations": {"name": "default", "contacts": []}
                    },
                    "ato": {
                        "id": "default",
                        "authorized": authorized_date,
                        "eol": eol_date,
                        "last_touch": current_time
                    },
                    "providers": {"name": [], "regions": []}
                }
            else:
                # Update ATO dates in existing project data
                compliance_data["project"]["ato"] = {
                    "id": ato_data.get("id", "dev"),
                    "authorized": authorized_date,
                    "eol": eol_date,
                    "last_touch": current_time
                }

            if "fisma" not in compliance_data:
                compliance_data["fisma"] = {"level": "moderate", "mode": "warn"}

            if "nist" not in compliance_data:
                compliance_data["nist"] = {"auxiliary": [], "exceptions": []}

            return cls(**compliance_data)

        except Exception as e:
            log.error(f"Failed to load compliance config: {str(e)}")
            # Return default config
            return cls.create_default()

    @classmethod
    def create_default(cls) -> "ComplianceConfig":
        """
        Create a default compliance configuration.

        Returns:
            ComplianceConfig: Default configuration instance
        """
        timestamp = datetime.now(timezone.utc)
        current_time = timestamp.isoformat()

        return cls(
            project=ScipConfig(
                environment="dev",
                production=False,
                ownership={
                    "owner": {"name": "default", "contacts": []},
                    "operations": {"name": "default", "contacts": []}
                },
                ato={
                    "id": "default",
                    "authorized": current_time,
                    "eol": (timestamp + timedelta(hours=24)).isoformat(),
                    "last_touch": current_time
                },
                providers={"name": [], "regions": []}
            ),
            fisma=FismaConfig(
                level="low",
                mode="warn"
            ),
            nist=NistConfig(
                auxiliary=[],
                exceptions=[]
            )
        )

    def model_dump(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "project": self.project.model_dump(),
            "fisma": self.fisma.model_dump(),
            "nist": self.nist.model_dump()
        }
