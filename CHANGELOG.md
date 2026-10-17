# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — 2026-10-17

### Added

- **Skill discovery**: Walks any local repository path to find `SKILL.md` files at
  arbitrary depth, solving the GitHub CLI layout limitation where skills under
  topic folders (e.g. `performance/r8-analyzer/SKILL.md`) are invisible to
  `gh skill install`.
- **SKILL.md parser**: Extracts YAML frontmatter (name, scope, title,
  description, tags) and Markdown body with fallbacks to directory-derived
  values.
- **TF-IDF semantic search engine**: Deterministic offline search using
  cosine similarity over multi-field skill metadata (title, description,
  tags, scope, body). Includes domain keyword expansion for Android
  development terminology (e.g. "r8" → "optimization", "shrinking").
- **SQLite persistence**: SQLAlchemy ORM models with UTC timestamps,
  JSON-encoded tags, and an audit log table.
- **FastAPI backend**: Endpoints for health check, indexing, searching,
  listing, skill detail retrieval, and audit log. All parameters validated.
- **React + TypeScript frontend**: Vite-built dashboard with search, list,
  detail, and index workflows. Loading, error, and empty states throughout.
- **Tests**: 66 backend pytest tests (discovery, parser, search, indexer, API)
  and 18 frontend Vitest tests (App, SkillSearch, SkillCard, Indexer).
- **Docker**: Backend (Python slim, nonroot) and frontend (nginx, nonroot)
  multi-stage Dockerfiles with healthchecks.
- **Docker Compose**: Backend, frontend, Keycloak (planned auth), and ntfy
  services with persistent volumes and 127.0.0.1 port binding.
- **CI**: GitHub Actions workflow for backend tests, frontend tests+build,
  and Docker builds on `ubuntu-latest`.
- **Documentation**: README with install/run/test steps, architecture
  Mermaid diagram, API reference, and AI/ML evaluation section.

### Planned (not yet implemented)

- Keycloak OIDC authorization-code login with PKCE and role-based auth
- LLM advisory explanations with multi-provider support
- Skill installation and preview workflows
- SAML identity brokering