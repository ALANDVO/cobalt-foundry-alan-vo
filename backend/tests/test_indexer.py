"""Tests for the SkillIndexer orchestrator."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.skill import Skill, AuditLog
from app.schemas.skill import IndexResult
from app.services.indexer import SkillIndexer
from app.services.search import TFIDFIndex


class TestIndexRepo:
    def test_indexes_all_skills_from_sample_repo(self, indexer: SkillIndexer, sample_repo: Path):
        """The indexer should discover and persist all 4 skills from the sample repo."""
        result, index = indexer.index_repo(str(sample_repo))

        assert result.discovered == 4
        assert result.indexed == 4
        assert len(result.skills) == 4
        assert len(index.documents) == 4

    def test_persists_skills_in_database(self, indexer: SkillIndexer, sample_repo: Path):
        """Indexed skills should be persisted in the database."""
        indexer.index_repo(str(sample_repo))
        skills = indexer.db.query(Skill).all()
        assert len(skills) == 4
        ids = {s.id for s in skills}
        assert "performance/r8-analyzer" in ids
        assert "ads/admob-integration" in ids
        assert "lint/lint-rules" in ids
        assert "devtools/android-cli" in ids

    def test_skill_records_have_timestamps(self, indexer: SkillIndexer, sample_repo: Path):
        """Skill records should have UTC timestamps."""
        indexer.index_repo(str(sample_repo))
        skill = indexer.db.get(Skill, "performance/r8-analyzer")
        assert skill is not None
        assert skill.created_at is not None
        # Should be timezone-aware UTC
        if skill.created_at.tzinfo is None:
            pytest.fail("created_at should be timezone-aware")
        assert skill.created_at.tzinfo.utcoffset(skill.created_at) is not None

    def test_audit_log_created(self, indexer: SkillIndexer, sample_repo: Path):
        """An audit-log entry should be created after indexing."""
        indexer.index_repo(str(sample_repo))
        logs = indexer.db.query(AuditLog).all()
        assert len(logs) == 1
        assert logs[0].action == "index_repo"

    def test_tags_stored_as_json(self, indexer: SkillIndexer, sample_repo: Path):
        """Tags should be stored as JSON in the database."""
        indexer.index_repo(str(sample_repo))
        skill = indexer.db.get(Skill, "performance/r8-analyzer")
        assert skill is not None
        assert skill.tag_list == ["android", "r8", "performance", "optimization", "shrinking", "debugging"]

    def test_reindex_updates_existing(self, indexer: SkillIndexer, sample_repo: Path):
        """Re-indexing the same repo should update, not duplicate, records."""
        indexer.index_repo(str(sample_repo))
        count_before = indexer.db.query(Skill).count()
        indexer.index_repo(str(sample_repo))
        count_after = indexer.db.query(Skill).count()
        assert count_before == count_after
        assert count_after == 4

    def test_rebuild_search_index_from_db(self, indexer: SkillIndexer, sample_repo: Path):
        """The search index should be rebuilt from database records after indexing."""
        result, index = indexer.index_repo(str(sample_repo))
        assert isinstance(index, TFIDFIndex)
        assert index.n_docs == 4

    def test_search_after_index(self, indexer: SkillIndexer, sample_repo: Path):
        """After indexing, searching should find relevant skills."""
        indexer.index_repo(str(sample_repo))
        # Search for something related to R8 optimization
        results = indexer.search_index.search("optimization shrinking")
        assert len(results) > 0
        # The R8 analyzer should be highly ranked
        r8_score = next((score for doc_id, score in results if doc_id == "performance/r8-analyzer"), 0)
        assert r8_score > 0

    def test_search_keyword_expansion_works(self, indexer: SkillIndexer, sample_repo: Path):
        """Searching 'r8' should find the R8 skill via keyword expansion."""
        indexer.index_repo(str(sample_repo))
        results = indexer.search_index.search("r8")
        ids = [doc_id for doc_id, _ in results]
        assert "performance/r8-analyzer" in ids