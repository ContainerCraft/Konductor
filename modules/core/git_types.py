from pydantic import BaseModel, Field
from typing import Dict, Any


class GitInfo(BaseModel):
    """Git repository information"""

    commit_hash: str = Field(default="unknown")
    branch_name: str = Field(default="unknown")
    remote_url: str = Field(default="unknown")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "commit": self.commit_hash,
            "branch": self.branch_name,
            "remote": self.remote_url,
        }
