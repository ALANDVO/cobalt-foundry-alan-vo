"""Tests for the TF-IDF semantic search engine."""
import pytest

from app.services.search import (
    TFIDFIndex,
    KEYWORD_EXPANSIONS,
    STOP_WORDS,
    tokenize,
    expand_keywords,
)


class TestTokenize:
    def test_lowercases_tokens(self):
        assert tokenize("Hello World") == ["hello", "world"]

    def test_filters_stop_words(self):
        tokens = tokenize("the quick brown fox")
        assert "the" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens
        assert "fox" in tokens

    def test_extracts_alphanumeric_only(self):
        tokens = tokenize("R8-optimization v2.0!")
        assert "r8" in tokens
        assert "optimization" in tokens
        assert "v2" in tokens

    def test_filters_single_char_tokens(self):
        tokens = tokenize("a b c hello")
        assert "hello" in tokens
        assert "a" not in tokens
        assert "b" not in tokens
        assert "c" not in tokens

    def test_empty_string_returns_empty(self):
        assert tokenize("") == []


class TestExpandKeywords:
    def test_expands_known_keyword(self):
        tokens = expand_keywords(["r8"])
        assert "r8" in tokens
        assert "optimization" in tokens

    def test_does_not_expand_unknown(self):
        tokens = expand_keywords(["quantum"])
        assert tokens == ["quantum"]

    def test_expands_multiple_keywords(self):
        tokens = expand_keywords(["ads", "r8"])
        assert "admob" in tokens
        assert "monetization" in tokens
        assert "optimization" in tokens

    def test_expansion_is_additive(self):
        tokens = ["ads"]
        expanded = expand_keywords(tokens)
        # Original token should still be present
        assert "ads" in expanded
        # Synonym should be added
        assert "admob" in expanded
        assert len(expanded) > len(tokens)


class TestTFIDFIndex:
    @pytest.fixture
    def populated_index(self) -> TFIDFIndex:
        index = TFIDFIndex()
        index.add("perf:r8", "R8 optimization shrinking obfuscation android performance")
        index.add("ads:admob", "AdMob monetization banner interstitial rewarded ads android")
        index.add("lint:rules", "Android Lint static analysis code quality rules kotlin")
        return index

    def test_is_empty_on_creation(self):
        index = TFIDFIndex()
        assert index.is_empty()

    def test_is_not_empty_after_add(self, populated_index):
        assert not populated_index.is_empty()

    def test_search_returns_ranked_results(self, populated_index):
        """Searching for 'optimization' should rank the R8 skill highest."""
        results = populated_index.search("optimization")
        assert len(results) > 0
        assert results[0][0] == "perf:r8"
        assert results[0][1] > 0

    def test_search_with_keyword_expansion(self, populated_index):
        """Searching 'r8' should find the R8 skill via keyword expansion."""
        results = populated_index.search("r8")
        ids = [doc_id for doc_id, _ in results]
        assert "perf:r8" in ids

    def test_search_no_results(self, populated_index):
        """A query with no matching terms should return an empty list."""
        results = populated_index.search("nonexistentterm")
        assert results == []

    def test_search_empty_index(self):
        """Searching an empty index returns no results."""
        index = TFIDFIndex()
        assert index.search("anything") == []

    def test_search_empty_query(self, populated_index):
        """An empty query should return no results."""
        results = populated_index.search("")
        assert results == []

    def test_search_stop_word_only_query(self, populated_index):
        """A query of only stop words should return no results."""
        results = populated_index.search("the and or")
        assert results == []

    def test_deterministic_ranking(self, populated_index):
        """The same query and index should always produce the same ranking."""
        r1 = populated_index.search("android ads monetization")
        r2 = populated_index.search("android ads monetization")
        assert r1 == r2

    def test_top_k_limits_results(self, populated_index):
        """top_k should cap the number of returned results."""
        results = populated_index.search("android", top_k=1)
        assert len(results) <= 1

    def test_scores_in_valid_range(self, populated_index):
        """All scores should be non-negative."""
        results = populated_index.search("optimiz")
        for _, score in results:
            assert score >= 0.0

    def test_build_text_weights_fields(self):
        """build_text should repeat fields proportionally to weight."""
        index = TFIDFIndex()
        text = index.build_text(
            title="R8 Optimization",
            description="Analyze optimization decisions",
            tags="r8 performance optimization",
            scope="performance",
            body="R8 is the default optimizer",
        )
        # Title has weight 3, so "R8 Optimization" should appear 3 times
        assert text.count("R8 Optimization") == 3

    def test_idf_is_zero_for_unseen_term(self):
        """IDF for a term not in any document should be 0 (no contribution)."""
        index = TFIDFIndex()
        index.add("d1", "hello world")
        assert index.idf("unseen_term") == 0.0

    def test_idf_increases_as_doc_frequency_decreases(self):
        """Rare terms should have higher IDF than common terms."""
        index = TFIDFIndex()
        index.add("d1", "common rareterm")
        index.add("d2", "common")
        assert index.idf("rareterm") > index.idf("common")