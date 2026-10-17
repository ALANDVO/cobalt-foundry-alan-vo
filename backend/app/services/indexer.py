"""Orchestrates discovery, parsing, persistence, and search-index building.

The :class:`SkillIndexer` ties together the filesystem walker, the SKILL.md
parser, the SQLAlchemy session, and the TF-IDF search engine into a single
transactional operation.  After indexing, the TF-IDF index is rebuilt from the
database so that subsequent searches reflect the latest data.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .discovery import DiscoveredSkill, discover_skills
from .parser import parse_skill_md
from .search import TFIDFIndex
from ..models.skill import AuditLog, Skill
from ..core.exceptions import SkillDiscoveryError
from ..schemas.skill import IndexResult


class SkillIndexer:
    """Index skills from a repository path into the database and search engine."""

    def __init__(self, db: Session):
        self.db = db
        self._search_index: TFIDFIndex | None = None

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_repo(self, repo_path: str) -> tuple[IndexResult, TFIDFIndex]:
        """Discover, parse, and persist all skills under *repo_path*.

        Returns the indexing result and a freshly rebuilt search index.
        Raises :class:`SkillDiscoveryError` if the path is inaccessible.
        """
        discovered = discover_skills(repo_path)

        skill_ids: list[str] = []
        for ds in discovered:
            parsed = parse_skill_md(ds.path, ds.scope, ds.name_hint)
            skill = self._upsert_skill(parsed, repo_path)
            skill_ids.append(skill.id)

        # Audit log entry.
        audit = AuditLog.for_index(repo_path, len(discovered), len(skill_ids))
        self.db.add(audit)

        self.db.commit()

        # Rebuild the search index from the database.
        search_index = self.rebuild_search_index()

        result = IndexResult(
            repo_path=repo_path,
            discovered=len(discovered),
            indexed=len(skill_ids),
            skills=skill_ids,
        )
        return result, search_index

    def _upsert_skill(self, parsed, repo_path: str) -> Skill:
        """Insert or update a Skill record in the database."""
        skill_id = f"{parsed.scope}/{parsed.name}"
        existing = self.db.get(Skill, skill_id)
        if existing:
            existing.title = parsed.title
            existing.description = parsed.description
            existing.tags = json.dumps(parsed.tags)
            existing.body = parsed.body
            existing.source_path = parsed.source_path
            existing.repo_path = repo_path
        else:
            skill = Skill(
                id=skill_id,
                name=parsed.name,
                scope=parsed.scope,
                title=parsed.title,
                description=parsed.description,
                tags=json.dumps(parsed.tags),
                body=parsed.body,
                source_path=parsed.source_path,
                repo_path=repo_path,
            )
            self.db.add(skill)
        self.db.flush()
        return self.db.get(Skill, skill_id)

    # ------------------------------------------------------------------
    # Search index
    # ------------------------------------------------------------------

    def rebuild_search_index(self) -> TFIDFIndex:
        """Build a new TF-IDF index from all skills in the database."""
        index = TFIDFIndex()
        skills = self.db.query(Skill).all()
        for skill in skills:
            text = index.build_text(
                title=skill.title,
                description=skill.description,
                tags=" ".join(skill.tag_list),
                scope=skill.scope,
                body=skill.body,
            )
            index.add(skill.id, text)
        self._search_index = index
        return index

    @property
    def search_index(self) -> TFIDFIndex:
        """Lazy-build the search index if it does not yet exist."""
        if self._search_index is None:
            self._search_index = self.rebuild_search_index()
        return self._search_index


__all__ = ["SkillIndexer"]