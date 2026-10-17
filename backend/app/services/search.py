"""Deterministic offline TF-IDF semantic search engine.

Indexes skill metadata (title, description, tags, scope, body) using TF-IDF
vectors with cosine similarity ranking.  Includes domain-specific keyword
expansion for Android development terminology to improve recall when users
describe a task in natural language rather than knowing the exact skill name.

No LLM key is required.  The algorithm is fully deterministic: given the same
index and query, the ranking is always identical.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

# Common English stop words — filtered before indexing or querying.
STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "them", "their", "what", "which", "who", "how", "when", "where",
    "why", "new", "such", "not", "no", "so", "than", "then", "its",
    "as", "also", "into", "out", "up", "down", "about", "above", "below",
})

# Domain keyword expansion: maps an abbreviation or common term to synonyms
# that should also match when the user includes the key term in their query.
KEYWORD_EXPANSIONS: dict[str, list[str]] = {
    "adb": ["android-debug-bridge", "debug-bridge", "debugging"],
    "agy": ["agent"],
    "apk": ["app-bundle", "application-package", "application"],
    "cli": ["command-line", "command-line-interface"],
    "gh": ["github"],
    "gradle": ["build-system", "build", "build-tool"],
    "jetpack": ["androidx", "android-libraries"],
    "lint": ["static-analysis", "code-analysis", "checker", "static"],
    "ndk": ["native-development-kit", "c++", "jni", "native"],
    "proguard": ["obfuscation", "shrinking", "minification", "minify"],
    "r8": ["optimization", "optimizer", "shrinking", "obfuscation", "code-shrinking"],
    "sdk": ["software-development-kit", "api-level"],
    "xml": ["markup-language"],
    "ads": ["admob", "monetization", "revenue", "banner", "interstitial", "rewarded"],
    "compose": ["jetpack-compose", "ui", "declarative", "kotlin-compose"],
    "kotlin": ["jvm", "language", "kotlin-language"],
    "coroutines": ["async", "asynchronous", "concurrency"],
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, extract alphanumeric tokens, filter stop words and short tokens."""
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def expand_keywords(tokens: list[str]) -> list[str]:
    """Append domain-specific synonyms for any recognized keyword."""
    expanded = list(tokens)
    for token in tokens:
        if token in KEYWORD_EXPANSIONS:
            expanded.extend(KEYWORD_EXPANSIONS[token])
    return expanded


@dataclass
class _Document:
    doc_id: str
    tf: Counter
    norm: float


@dataclass
class TFIDFIndex:
    """In-memory TF-IDF index with cosine-similarity search.

    Documents are added via :meth:`add`, which tokenizes the text, applies
    keyword expansion, and records term frequencies.  Searches are performed
    via :meth:`search`, returning ``(doc_id, score)`` pairs sorted by
    descending relevance.
    """

    documents: dict[str, _Document] = field(default_factory=dict)
    df: Counter = field(default_factory=Counter)
    n_docs: int = 0

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add(self, doc_id: str, text: str) -> None:
        """Add a document to the index."""
        tokens = expand_keywords(tokenize(text))
        if not tokens:
            tf: Counter = Counter()
            norm = 0.0
        else:
            tf = Counter(tokens)
            norm = math.sqrt(sum(v ** 2 for v in tf.values()))
        self.documents[doc_id] = _Document(doc_id, tf, norm)
        for term in tf:
            self.df[term] += 1
        self.n_docs += 1

    def is_empty(self) -> bool:
        return self.n_docs == 0

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def idf(self, term: str) -> float:
        """Smoothed inverse document frequency for *term*."""
        df = self.df.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self.n_docs + 1) / (df + 1)) + 1.0

    def build_text(self, **fields: str | None) -> str:
        """Combine multiple text fields into a single weighted search string.

        Fields are repeated proportionally to their importance so that titles
        contribute more to the TF-IDF vectors than bodies.
        """
        parts: list[str] = []
        weights = {
            "title": 3,
            "description": 2,
            "tags": 2,
            "scope": 2,
            "body": 1,
        }
        for field_name, weight in weights.items():
            value = fields.get(field_name)
            if value:
                parts.extend([value] * weight)
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 20) -> list[tuple[str, float]]:
        """Return the top-*k* documents ranked by cosine similarity to *query*.

        Returns an empty list when the index is empty or no documents match.
        """
        if self.n_docs == 0:
            return []

        q_tokens = expand_keywords(tokenize(query))
        if not q_tokens:
            return []
        q_tf = Counter(q_tokens)
        q_norm = math.sqrt(sum(v ** 2 for v in q_tf.values()))
        if q_norm == 0:
            return []

        # Pre-compute TF-IDF vector norms for documents containing query terms.
        scores: dict[str, float] = {}
        for doc_id, doc in self.documents.items():
            if not doc.tf:
                continue
            dot = 0.0
            for term, q_count in q_tf.items():
                if term in doc.tf:
                    idf_val = self.idf(term)
                    dot += q_count * doc.tf[term] * idf_val * idf_val
            if dot > 0:
                scores[doc_id] = dot / (q_norm * doc.norm)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:top_k]


__all__ = ["TFIDFIndex", "tokenize", "expand_keywords", "KEYWORD_EXPANSIONS"]