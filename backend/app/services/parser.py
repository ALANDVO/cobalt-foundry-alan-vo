"""SKILL.md parser.

Extracts YAML frontmatter (name, scope, title, description, tags) and the
Markdown body from a discovered SKILL.md file.  Falls back to deriving values
from the directory structure when frontmatter is absent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..core.exceptions import SkillParseError

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


@dataclass
class ParsedSkill:
    """A fully parsed skill ready for persistence."""

    name: str
    scope: str
    title: str
    description: str | None
    tags: list[str] = field(default_factory=list)
    body: str = ""
    source_path: str = ""


def parse_skill_md(
    path: Path,
    scope: str,
    name_hint: str | None = None,
) -> ParsedSkill:
    """Parse a single SKILL.md file into a :class:`ParsedSkill`."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SkillParseError(f"Cannot read {path}: {exc}") from exc

    frontmatter: dict = {}
    body = raw

    fm_match = _FRONTMATTER_RE.match(raw)
    if fm_match:
        try:
            frontmatter = yaml.safe_load(fm_match.group(1)) or {}
        except yaml.YAMLError as exc:
            raise SkillParseError(f"Invalid YAML frontmatter in {path}: {exc}") from exc
        body = raw[fm_match.end():]

    name = frontmatter.get("name") or name_hint or path.parent.name
    scope = frontmatter.get("scope") or scope
    title = frontmatter.get("title") or _extract_title(body) or name

    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif not isinstance(tags, list):
        tags = []

    description = frontmatter.get("description")

    return ParsedSkill(
        name=str(name),
        scope=scope,
        title=str(title),
        description=str(description) if description else None,
        tags=[str(t) for t in tags],
        body=body,
        source_path=str(path),
    )


def _extract_title(body: str) -> str | None:
    """Extract the first Markdown H1 title from the body."""
    match = _TITLE_RE.match(body.strip())
    if match:
        return match.group(1).strip()
    return None


__all__ = ["ParsedSkill", "parse_skill_md"]