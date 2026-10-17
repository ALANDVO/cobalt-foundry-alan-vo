"""Pydantic schemas for the skill discovery API."""
import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    scope: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4096)
    tags: list[str] = Field(default_factory=list, max_length=32)
    body: str | None = Field(default=None, max_length=65536)
    source_path: str = Field(..., min_length=1, max_length=512)
    repo_path: str = Field(..., min_length=1, max_length=1024)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Accept either a list or a JSON string (as stored in SQLite)."""
        if isinstance(v, str):
            return json.loads(v)
        return v


class SkillCreate(SkillBase):
    """Payload for creating a single skill record."""


class SkillRead(SkillBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillSearchHit(BaseModel):
    id: str
    name: str
    scope: str
    title: str
    description: str | None = None
    score: float = Field(..., ge=0.0, le=1.0)
    source_path: str


class SkillSearchResponse(BaseModel):
    query: str
    total: int
    hits: list[SkillSearchHit]


class IndexResult(BaseModel):
    repo_path: str
    discovered: int
    indexed: int
    skills: list[str]


class SkillIndexRequest(BaseModel):
    repo_path: str = Field(..., min_length=1, max_length=2048)


class AuditLogRead(BaseModel):
    id: int
    action: str
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class QualityMetrics(BaseModel):
    skill_id: str
    completeness: float
    description_length: int
    tag_count: int
    body_words: int
    overall_score: float


class QualityResponse(BaseModel):
    total: int
    metrics: list[QualityMetrics]