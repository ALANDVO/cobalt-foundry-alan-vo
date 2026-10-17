"""SQLAlchemy ORM models for skills and audit logs."""
import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text

from ..core.database import Base, UTCDateTime


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class Skill(Base):
    """A parsed GitHub CLI skill discovered from a SKILL.md file."""

    __tablename__ = "skills"

    id: str = Column(String, primary_key=True, index=True)  # "scope/name"
    name: str = Column(String, nullable=False)
    scope: str = Column(String, nullable=False, index=True)
    title: str = Column(String, nullable=False)
    description: str | None = Column(Text, nullable=True)
    tags: str = Column(Text, nullable=False, default="[]")  # JSON-encoded list
    body: str | None = Column(Text, nullable=True)
    source_path: str = Column(String, nullable=False)
    repo_path: str = Column(String, nullable=False, index=True)
    created_at: datetime = Column(UTCDateTime, default=_utcnow)
    updated_at: datetime = Column(UTCDateTime, default=_utcnow, onupdate=_utcnow)

    @property
    def tag_list(self) -> list[str]:
        """Parse the stored JSON tags back into a list."""
        return json.loads(self.tags) if self.tags else []


class AuditLog(Base):
    """An audit trail of indexing and search operations."""

    __tablename__ = "audit_log"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    action: str = Column(String, nullable=False, index=True)
    detail: str = Column(Text, nullable=False)  # JSON
    created_at: datetime = Column(UTCDateTime, default=_utcnow)

    @classmethod
    def for_index(cls, repo_path: str, discovered: int, indexed: int) -> "AuditLog":
        entry = cls(action="index_repo", detail=json.dumps({
            "repo_path": repo_path,
            "discovered": discovered,
            "indexed": indexed,
        }))
        return entry


__all__ = ["Skill", "AuditLog"]