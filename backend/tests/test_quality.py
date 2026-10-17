"""Tests for the skill quality assessment engine."""
import pytest

from app.services.quality import assess_all, assess_skill, SkillQuality

class TestAssessSkill:
    def test_full_skill_gets_high_score(self):
        """A skill with all fields populated should score highest."""
        q = assess_skill(
            "perf:r8",
            "R8 Optimization Analyzer",
            "Analyze R8 optimization decisions across the Android toolchain.",
            ["android", "r8", "optimization"],
            "R8 is Android's default optimizer and compiler. " * 20,
        )
        assert q.completeness == 1.0
        assert q.overall_score > 0.5
        assert q.description_length > 50
        assert q.tag_count == 3
        assert q.body_words > 100

    def test_empty_skill_gets_low_score(self):
        """A skill with no optional fields should score low."""
        q = assess_skill("test:empty", "Empty", None, [], "")
        assert q.completeness == 0.0
        assert q.tag_count == 0
        assert q.description_length == 0
        assert q.body_words == 0
        assert q.overall_score < 0.5

    def test_partial_completeness(self):
        """A skill with only description should have 0.33 completeness."""
        q = assess_skill("test:partial", "Partial", "A description.", ["tag"], None)
        assert q.completeness == pytest.approx(2 / 3, abs=1e-3)
        assert q.body_words == 0

    def test_long_description_scores_higher(self):
        """A longer description should contribute more to the overall score."""
        short = assess_skill("a:test", "Short", "A.", ["tag"], "body")
        long_desc = "This is a much longer and more detailed description of the skill." * 3
        long = assess_skill("b:test", "Long", long_desc, ["tag"], "body")
        assert long.description_length > short.description_length
        assert long.overall_score > short.overall_score

    def test_many_tags_improve_score(self):
        """More tags should improve the tag component of the score."""
        few = assess_skill("a:test", "Few", "desc", ["tag"], "body")
        many = assess_skill("b:test", "Many", "desc", ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"], "body")
        assert many.tag_count > few.tag_count
        assert many.overall_score >= few.overall_score

    def test_deterministic(self):
        """Same inputs should always produce the same metrics."""
        result1 = assess_skill(
            "perf:r8", "R8", "Analyze optimization.", ["android", "r8"], "R8 body"
        )
        result2 = assess_skill(
            "perf:r8", "R8", "Analyze optimization.", ["android", "r8"], "R8 body"
        )
        assert result1 == result2

    def test_to_dict(self):
        """to_dict should return all fields as a dictionary."""
        q = assess_skill("test:t", "Title", "desc", ["tag"], "body")
        d = q.to_dict()
        assert d["skill_id"] == "test:t"
        assert "completeness" in d
        assert "overall_score" in d
        assert d["tag_count"] == 1


class TestAssessAll:
    def test_sorts_by_score_descending(self):
        """assess_all should sort by overall_score descending."""
        skills = [
            ("a:test", "Low", None, [], None),
            ("b:test", "High", "A detailed description here.", ["t1", "t2"], "Body text here."),
        ]
        results = assess_all(skills)
        assert results[0].skill_id == "b:test"
        assert results[1].skill_id == "a:test"
        assert results[0].overall_score > results[1].overall_score

    def test_empty_input(self):
        """assess_all with no skills should return empty list."""
        assert assess_all([]) == []

    def test_single_skill(self):
        """assess_all with one skill should return one result."""
        results = assess_all([("a:t", "Title", "desc", ["tag"], "body")])
        assert len(results) == 1
        assert results[0].skill_id == "a:t"