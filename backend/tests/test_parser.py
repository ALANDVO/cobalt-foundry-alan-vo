"""Tests for the SKILL.md parser."""
from pathlib import Path

import pytest

from app.services.discovery import DiscoveredSkill
from app.services.parser import parse_skill_md, ParsedSkill
from app.core.exceptions import SkillParseError


class TestParseSkillMd:
    def test_parses_frontmatter_and_body(self, sample_repo: Path):
        """The parser should extract frontmatter fields and the Markdown body."""
        path = sample_repo / "performance/r8-analyzer/SKILL.md"
        parsed = parse_skill_md(path, scope="performance", name_hint="r8-analyzer")

        assert parsed.name == "r8-analyzer"
        assert parsed.scope == "performance"
        assert parsed.title == "R8 Optimization Analyzer"
        assert parsed.description is not None
        assert "R8" in parsed.description
        assert "optimization" in parsed.description
        assert "r8" in parsed.tags
        assert "performance" in parsed.tags
        assert "# R8 Analyzer Skill" in parsed.body

    def test_uses_name_hint_when_no_frontmatter_name(self, tmp_path: Path):
        """When frontmatter lacks 'name', use the name_hint from discovery."""
        md = tmp_path / "test_skill.md"
        md.write_text(
            "---\n"
            "title: Test Skill\n"
            "description: A test skill\n"
            "---\n"
            "# Test Skill\n"
            "Body text here.\n"
        )
        parsed = parse_skill_md(md, scope="test", name_hint="my-skill")
        assert parsed.name == "my-skill"
        assert parsed.title == "Test Skill"
        assert parsed.description == "A test skill"

    def test_falls_back_to_directory_name(self, tmp_path: Path):
        """When no name or hint is available, use the parent directory name."""
        md = tmp_path / "custom" / "SKILL.md"
        md.parent.mkdir(parents=True)
        md.write_text(
            "---\n"
            "title: Custom Skill\n"
            "---\n"
            "# Custom Skill\n"
        )
        parsed = parse_skill_md(md, scope="test", name_hint="")
        assert parsed.name == "custom"

    def test_parses_tags_as_list(self, tmp_path: Path):
        """Tags provided as a YAML list should be parsed into a Python list."""
        md = tmp_path / "t.md"
        md.write_text(
            "---\n"
            "name: tagged\n"
            "scope: test\n"
            "title: Tagged\n"
            "tags:\n"
            "  - android\n"
            "  - r8\n"
            "---\n"
            "# Tagged\n"
        )
        parsed = parse_skill_md(md, scope="test", name_hint="tagged")
        assert parsed.tags == ["android", "r8"]

    def test_parses_tags_as_string(self, tmp_path: Path):
        """Tags provided as a comma-separated string should be split."""
        md = tmp_path / "t.md"
        md.write_text(
            "---\n"
            "name: tagged\n"
            "scope: test\n"
            "title: Tagged\n"
            "tags: android, r8, testing\n"
            "---\n"
            "# Tagged\n"
        )
        parsed = parse_skill_md(md, scope="test", name_hint="tagged")
        assert parsed.tags == ["android", "r8", "testing"]

    def test_no_frontmatter(self, tmp_path: Path):
        """A SKILL.md without frontmatter should still parse (title from H1)."""
        md = tmp_path / "SKILL.md"
        md.write_text(
            "# My Skill\n"
            "This is the body with no frontmatter.\n"
        )
        parsed = parse_skill_md(md, scope="root", name_hint="my-skill")
        assert parsed.name == "my-skill"
        assert parsed.title == "My Skill"
        assert parsed.description is None
        assert parsed.tags == []

    def test_invalid_yaml_raises(self, tmp_path: Path):
        """Malformed YAML frontmatter should raise SkillParseError."""
        md = tmp_path / "bad.md"
        md.write_text(
            "---\n"
            "name: [unterminated\n"
            "---\n"
            "# Bad\n"
        )
        with pytest.raises(SkillParseError):
            parse_skill_md(md, scope="test", name_hint="bad")

    def test_empty_description_is_none(self, tmp_path: Path):
        """An empty description field should be stored as None."""
        md = tmp_path / "t.md"
        md.write_text(
            "---\n"
            "name: t\n"
            "title: T\n"
            "description: ''\n"
            "---\n"
            "# T\n"
        )
        parsed = parse_skill_md(md, scope="test", name_hint="t")
        assert parsed.description is None