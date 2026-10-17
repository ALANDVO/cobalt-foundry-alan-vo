"""Filesystem-based skill discovery.

Walks a repository directory tree (or any local path) to find SKILL.md files
at arbitrary depth, regardless of directory layout.  This solves the problem
that ``gh skill`` only discovers skills under a ``skills/`` directory prefix
while the upstream ``android/skills`` repo organizes them under topic folders
two or more levels deep.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..core.exceptions import SkillDiscoveryError


@dataclass(frozen=True)
class DiscoveredSkill:
    """A discovered SKILL.md file with derived scope and name hints."""

    path: Path
    relative_path: str
    scope: str
    name_hint: str


def discover_skills(repo_path: str | os.PathLike[str]) -> list[DiscoveredSkill]:
    """Walk *repo_path* recursively and return all SKILL.md files found.

    The scope is derived from the directory structure:
      - ``performance/r8-analyzer/SKILL.md`` → scope="performance"
      - ``skills/r8-analyzer/SKILL.md``      → scope=""
      - ``SKILL.md``                          → scope="root"

    Results are sorted by relative path for deterministic ordering.
    """
    root = Path(repo_path)
    if not root.is_dir():
        raise SkillDiscoveryError(f"Repository path is not a directory: {repo_path}")

    results: list[DiscoveredSkill] = []
    for path in sorted(root.rglob("SKILL.md")):
        rel = path.relative_to(root)
        scope, name_hint = _derive_scope_and_name(rel)
        results.append(DiscoveredSkill(
            path=path,
            relative_path=str(rel),
            scope=scope,
            name_hint=name_hint,
        ))
    return results


def _derive_scope_and_name(rel: Path) -> tuple[str, str]:
    """Derive scope and skill name from the relative path to SKILL.md."""
    parts = rel.parts
    # SKILL.md at the repository root.
    if len(parts) <= 1:
        return ("root", "")

    # Handle "skills/{scope?}/{name}/SKILL.md" layout used by gh-skill.
    if parts[0] == "skills" and len(parts) >= 3:
        scope = parts[1] if len(parts) >= 3 else ""
        name = parts[-2]
        return (scope, name)

    # If the parent directory is "skills", use the grandparent as scope.
    if parts[-2] == "skills" and len(parts) >= 3:
        return (parts[-3], parts[-2])

    # Default: first directory component is scope, last is name.
    scope = parts[0] if len(parts) >= 2 else ""
    name = parts[-2]
    return (scope, name)


__all__ = ["discover_skills", "DiscoveredSkill"]