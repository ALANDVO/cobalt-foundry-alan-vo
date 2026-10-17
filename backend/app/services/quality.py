"""Skill quality assessment engine.

Computes deterministic, data-driven metrics for each indexed skill so that
users can sort and filter by completeness and informational richness.  All
metrics are derived from the actual skill records — no external API calls or
LLM inference required.

Metrics:
  - completeness: fraction of optional fields present (description, tags, body)
  - description_length: character count of the description
  - tag_count: number of tags
  - body_words: word count of the Markdown body
  - overall_score: weighted geometric mean of normalised sub-scores
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass


# Weights for the overall score: completeness, description richness, tag
# coverage, and body content.  Sum to 1.0.
_WEIGHTS = {
    "completeness": 0.35,
    "description": 0.25,
    "tags": 0.15,
    "body": 0.25,
}

_WORD_RE = re.compile(r"\S+")


@dataclass
class SkillQuality:
    """Quality metrics for a single skill."""

    skill_id: str
    completeness: float  # 0.0–1.0
    description_length: int
    tag_count: int
    body_words: int
    overall_score: float  # 0.0–1.0

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "completeness": round(self.completeness, 4),
            "description_length": self.description_length,
            "tag_count": self.tag_count,
            "body_words": self.body_words,
            "overall_score": round(self.overall_score, 4),
        }


def assess_skill(
    skill_id: str,
    title: str,
    description: str | None,
    tags: list[str],
    body: str | None,
) -> SkillQuality:
    """Compute quality metrics for a single skill record.

    Args:
        skill_id: The skill's unique identifier (``scope/name``).
        title: Human-readable title.
        description: Short description, if present.
        tags: List of tag strings.
        body: Full Markdown body, if present.

    Returns:
        A :class:`SkillQuality` with normalised scores.
    """
    # Completeness: fraction of optional fields that are non-empty.
    fields_total = 3  # description, tags, body
    fields_present = 0
    if description and description.strip():
        fields_present += 1
    if tags and len(tags) > 0:
        fields_present += 1
    if body and body.strip():
        fields_present += 1
    completeness = fields_present / fields_total

    # Description richness: longer descriptions provide more signal.
    desc_len = len(description) if description else 0
    # A description of 120+ chars is "excellent", scaled linearly.
    desc_score = min(desc_len / 120.0, 1.0)

    # Tag coverage: more tags → better categorisation, capped at 8.
    tag_score = min(len(tags) / 8.0, 1.0)

    # Body richness: more words → more detail, capped at 200 words.
    body_words = 0
    if body:
        body_words = len(_WORD_RE.findall(body))
    body_score = min(body_words / 200.0, 1.0)

    # Overall: weighted geometric mean (avoids one zero killing the score).
    overall = (
        completeness ** _WEIGHTS["completeness"]
        * desc_score ** _WEIGHTS["description"]
        * tag_score ** _WEIGHTS["tags"]
        * body_score ** _WEIGHTS["body"]
    )
    # If any component is 0, the geometric mean is 0. Use arithmetic mean
    # as a fallback to avoid total-zero scores for partially-complete skills.
    if overall == 0.0:
        overall = (
            completeness * _WEIGHTS["completeness"]
            + desc_score * _WEIGHTS["description"]
            + tag_score * _WEIGHTS["tags"]
            + body_score * _WEIGHTS["body"]
        )

    return SkillQuality(
        skill_id=skill_id,
        completeness=round(completeness, 4),
        description_length=desc_len,
        tag_count=len(tags),
        body_words=body_words,
        overall_score=round(min(overall, 1.0), 4),
    )


def assess_all(skills: list[tuple[str, str, str | None, list[str], str | None]]) -> list[SkillQuality]:
    """Compute quality metrics for a batch of skills.

    Args:
        skills: List of (id, title, description, tags, body) tuples.

    Returns:
        List of :class:`SkillQuality`, sorted by overall_score descending.
    """
    results = [
        assess_skill(sid, title, desc, tags, body)
        for sid, title, desc, tags, body in skills
    ]
    results.sort(key=lambda q: q.overall_score, reverse=True)
    return results


__all__ = ["SkillQuality", "assess_skill", "assess_all"]