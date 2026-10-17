"""Tests for the filesystem-based skill discovery walker."""
from pathlib import Path

import pytest

from app.services.discovery import discover_skills, DiscoveredSkill
from app.core.exceptions import SkillDiscoveryError


class TestDiscoverSkills:
    def test_discovers_all_skill_md_files(self, sample_repo: Path):
        """The walker should find every SKILL.md at any depth."""
        results = discover_skills(sample_repo)
        # We have 4 SKILL.md files: root, performance/r8-analyzer, ads/admob, lint/rules
        assert len(results) == 4
        names = {r.relative_path for r in results}
        assert "SKILL.md" in names
        assert "performance/r8-analyzer/SKILL.md" in names
        assert "ads/admob/SKILL.md" in names
        assert "lint/rules/SKILL.md" in names

    def test_results_are_sorted_by_path(self, sample_repo: Path):
        """Results must be deterministically sorted."""
        results = discover_skills(sample_repo)
        paths = [r.relative_path for r in results]
        assert paths == sorted(paths)

    def test_scope_derived_from_directory(self, sample_repo: Path):
        """The scope should be the first directory component."""
        results = discover_skills(sample_repo)
        by_path = {r.relative_path: r for r in results}
        assert by_path["performance/r8-analyzer/SKILL.md"].scope == "performance"
        assert by_path["ads/admob/SKILL.md"].scope == "ads"
        assert by_path["lint/rules/SKILL.md"].scope == "lint"
        # Root-level SKILL.md has scope "root"
        assert by_path["SKILL.md"].scope == "root"

    def test_name_hint_derived_from_directory(self, sample_repo: Path):
        """The name hint should be the parent directory of SKILL.md."""
        results = discover_skills(sample_repo)
        by_path = {r.relative_path: r for r in results}
        assert by_path["performance/r8-analyzer/SKILL.md"].name_hint == "r8-analyzer"
        assert by_path["ads/admob/SKILL.md"].name_hint == "admob"
        assert by_path["lint/rules/SKILL.md"].name_hint == "rules"
        # Root level has no parent directory name hint
        assert by_path["SKILL.md"].name_hint == ""

    def test_raises_for_nonexistent_path(self, tmp_path: Path):
        """A path that does not exist should raise SkillDiscoveryError."""
        with pytest.raises(SkillDiscoveryError):
            discover_skills(str(tmp_path / "nonexistent"))

    def test_raises_for_file_not_directory(self, sample_repo: Path):
        """A file path (not a directory) should raise SkillDiscoveryError."""
        with pytest.raises(SkillDiscoveryError):
            discover_skills(str(sample_repo / "SKILL.md"))

    def test_empty_repo_returns_empty_list(self, tmp_path: Path):
        """An empty directory should return an empty list."""
        results = discover_skills(tmp_path)
        assert results == []


class TestDiscoveredSkill:
    def test_is_frozen_dataclass(self):
        """DiscoveredSkill should be immutable."""
        ds = DiscoveredSkill(
            path=Path("/tmp/SKILL.md"),
            relative_path="test/SKILL.md",
            scope="test",
            name_hint="test",
        )
        with pytest.raises(Exception):
            ds.scope = "changed"