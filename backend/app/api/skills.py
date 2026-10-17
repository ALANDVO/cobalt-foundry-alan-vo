"""API routes for skill discovery, indexing, search, and detail."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..models.skill import AuditLog, Skill
from ..schemas.skill import (
    AuditLogRead,
    HealthResponse,
    IndexResult,
    QualityMetrics,
    QualityResponse,
    SkillIndexRequest,
    SkillRead,
    SkillSearchHit,
    SkillSearchResponse,
)
from ..services.indexer import SkillIndexer
from ..services.quality import assess_all
from .deps import get_indexer

router = APIRouter(prefix="/api/v1", tags=["skills"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health-check endpoint."""
    return HealthResponse(status="ok", version=settings.version)


@router.post(
    "/skills/index",
    response_model=IndexResult,
    status_code=status.HTTP_201_CREATED,
)
def index_repo(
    request: SkillIndexRequest,
    indexer: SkillIndexer = Depends(get_indexer),
) -> IndexResult:
    """Discover and index all SKILL.md files under *request.repo_path*."""
    from ..core.exceptions import SkillDiscoveryError
    try:
        result, _ = indexer.index_repo(request.repo_path)
    except (FileNotFoundError, SkillDiscoveryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    return result


@router.get("/skills/search", response_model=SkillSearchResponse)
def search_skills(
    q: Annotated[str, Query(min_length=1, max_length=256)],
    indexer: SkillIndexer = Depends(get_indexer),
    top_k: int = Query(default=20, ge=1, le=100),
) -> SkillSearchResponse:
    """Semantic search for skills matching the natural-language query *q*."""
    index = indexer.search_index
    if index.is_empty():
        return SkillSearchResponse(query=q, total=0, hits=[])

    ranked = index.search(q, top_k=top_k)
    if not ranked:
        return SkillSearchResponse(query=q, total=0, hits=[])

    skill_ids = [doc_id for doc_id, _ in ranked]
    skills = indexer.db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    skill_map = {s.id: s for s in skills}

    hits: list[SkillSearchHit] = []
    for doc_id, score in ranked:
        skill = skill_map.get(doc_id)
        if skill is None:
            continue
        hits.append(SkillSearchHit(
            id=skill.id,
            name=skill.name,
            scope=skill.scope,
            title=skill.title,
            description=skill.description,
            score=round(min(score, 1.0), 4),
            source_path=skill.source_path,
        ))

    return SkillSearchResponse(query=q, total=len(hits), hits=hits)


@router.get("/skills", response_model=list[SkillRead])
def list_skills(
    db: Session = Depends(get_db),
    scope: str | None = Query(default=None, max_length=64),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[SkillRead]:
    """List all indexed skills, optionally filtered by scope."""
    query = db.query(Skill)
    if scope:
        query = query.filter(Skill.scope == scope)
    return query.order_by(Skill.scope, Skill.name).offset(skip).limit(limit).all()


@router.get("/skills/{skill_id:path}", response_model=SkillRead)
def get_skill(
    skill_id: str,
    db: Session = Depends(get_db),
) -> SkillRead:
    """Retrieve a single skill by its identifier (``scope/name``)."""
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill not found: {skill_id}",
        )
    return skill


@router.get("/audit-log", response_model=list[AuditLogRead])
def get_audit_log(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AuditLogRead]:
    """Return recent audit-log entries."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/metrics", response_model=QualityResponse)
def get_metrics(db: Session = Depends(get_db)) -> QualityResponse:
    """Compute quality metrics for all indexed skills.

    Returns completeness scores, description lengths, tag counts, body word
    counts, and an overall weighted score for each skill.  Fully deterministic
    and offline — derived from actual stored records.
    """
    skills = db.query(Skill).order_by(Skill.scope, Skill.name).all()
    tuples = [(s.id, s.title, s.description, s.tag_list, s.body) for s in skills]
    metrics = assess_all(tuples)
    return QualityResponse(
        total=len(metrics),
        metrics=[QualityMetrics(**m.to_dict()) for m in metrics],
    )