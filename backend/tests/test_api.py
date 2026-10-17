"""Integration tests for the FastAPI skill discovery API.

These tests cross the real HTTP boundary using FastAPI's TestClient (httpx).
"""
from pathlib import Path

import pytest

from conftest import SAMPLE_REPO


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        """GET /api/v1/health should return status ok and version."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestIndexEndpoint:
    def test_index_repo_creates_skills(self, client):
        """POST /api/v1/skills/index should discover and index all skills."""
        resp = client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        assert resp.status_code == 201
        data = resp.json()
        assert data["discovered"] == 4
        assert data["indexed"] == 4
        assert len(data["skills"]) == 4

    def test_index_nonexistent_repo_returns_404(self, client):
        """Indexing a nonexistent path should return 404."""
        resp = client.post("/api/v1/skills/index", json={"repo_path": "/nonexistent/repo"})
        assert resp.status_code == 404

    def test_index_creates_audit_log(self, client):
        """Indexing should create an audit-log entry."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/audit-log")
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 1
        assert logs[0]["action"] == "index_repo"

    def test_index_empty_request_body(self, client):
        """An empty request body should return a validation error (422)."""
        resp = client.post("/api/v1/skills/index", json={})
        assert resp.status_code == 422


class TestListSkillsEndpoint:
    def test_list_skills_after_index(self, client):
        """GET /api/v1/skills should return all indexed skills."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        skills = resp.json()
        assert len(skills) == 4

    def test_list_skills_empty(self, client):
        """Before indexing, GET /api/v1/skills should return an empty list."""
        resp = client.get("/api/v1/skills")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_skills_filtered_by_scope(self, client):
        """Filtering by scope should return only matching skills."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills?scope=performance")
        assert resp.status_code == 200
        skills = resp.json()
        assert len(skills) == 1
        assert skills[0]["scope"] == "performance"

    def test_list_skills_pagination(self, client):
        """Pagination parameters should limit returned results."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestSearchEndpoint:
    def test_search_finds_relevant_skills(self, client):
        """Searching for 'optimization' should find the R8 skill."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills/search?q=optimization")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        assert data["query"] == "optimization"
        # The first hit should be the R8 analyzer
        assert data["hits"][0]["id"] == "performance/r8-analyzer"

    def test_search_with_keyword_expansion(self, client):
        """Searching 'r8' should find R8-related skills via keyword expansion."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills/search?q=r8")
        assert resp.status_code == 200
        data = resp.json()
        hit_ids = [h["id"] for h in data["hits"]]
        assert "performance/r8-analyzer" in hit_ids

    def test_search_ads_monetization(self, client):
        """Searching for 'monetization' should find the AdMob skill."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills/search?q=monetization")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        hit_ids = [h["id"] for h in data["hits"]]
        assert "ads/admob-integration" in hit_ids

    def test_search_empty_query(self, client):
        """An empty query parameter should return 422 validation error."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills/search?q=")
        assert resp.status_code == 422

    def test_search_no_index_returns_empty(self, client):
        """Searching before indexing should return empty results."""
        resp = client.get("/api/v1/skills/search?q=anything")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["hits"] == []

    def test_search_results_have_scores(self, client):
        """Search hits should include a score in [0, 1]."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills/search?q=android")
        assert resp.status_code == 200
        for hit in resp.json()["hits"]:
            assert 0.0 <= hit["score"] <= 1.0


class TestSkillDetailEndpoint:
    def test_get_skill_by_id(self, client):
        """GET /api/v1/skills/{id} should return the skill."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/skills/performance/r8-analyzer")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "r8-analyzer"
        assert data["scope"] == "performance"
        assert data["title"] == "R8 Optimization Analyzer"

    def test_get_nonexistent_skill_returns_404(self, client):
        """A nonexistent skill ID should return 404."""
        resp = client.get("/api/v1/skills/nonexistent/skill")
        assert resp.status_code == 404


class TestEndToEndWorkflow:
    def test_index_then_search_then_detail(self, client):
        """Full workflow: index repo → search → retrieve detail."""
        repo = str(SAMPLE_REPO)

        # Step 1: Index
        resp = client.post("/api/v1/skills/index", json={"repo_path": repo})
        assert resp.status_code == 201
        indexed_ids = resp.json()["skills"]

        # Step 2: Search
        resp = client.get("/api/v1/skills/search?q=ads+banner+monetization")
        assert resp.status_code == 200
        search_data = resp.json()
        assert search_data["total"] > 0
        top_id = search_data["hits"][0]["id"]
        assert top_id in indexed_ids

        # Step 3: Get detail
        resp = client.get(f"/api/v1/skills/{top_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["title"] == search_data["hits"][0]["title"]


class TestMetricsEndpoint:
    def test_metrics_returns_quality_scores(self, client):
        """GET /api/v1/metrics should return quality metrics for indexed skills."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 4
        for m in data["metrics"]:
            assert "skill_id" in m
            assert 0.0 <= m["overall_score"] <= 1.0
            assert 0.0 <= m["completeness"] <= 1.0

    def test_metrics_empty(self, client):
        """Before indexing, metrics should return zero total."""
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["metrics"] == []

    def test_metrics_sorted_by_score(self, client):
        """Metrics should be sorted by overall_score descending."""
        client.post("/api/v1/skills/index", json={"repo_path": str(SAMPLE_REPO)})
        resp = client.get("/api/v1/metrics")
        data = resp.json()
        scores = [m["overall_score"] for m in data["metrics"]]
        assert scores == sorted(scores, reverse=True)