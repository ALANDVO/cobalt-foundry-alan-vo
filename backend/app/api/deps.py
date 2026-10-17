"""FastAPI dependencies: database session and skill indexer."""
from fastapi import Depends
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.indexer import SkillIndexer


def get_indexer(db: Session = Depends(get_db)) -> SkillIndexer:
    """Create a SkillIndexer bound to the current database session.

    The TF-IDF search index is rebuilt from the database on first query, so it
    always reflects persisted state.  For higher throughput an external cache
    (e.g., Redis) would be layered in — see docs/architecture.md.
    """
    return SkillIndexer(db)


__all__ = ["get_indexer", "get_db"]