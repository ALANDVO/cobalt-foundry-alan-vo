# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skill-quality-metrics

## Roadmap

### skill-discovery — Skill discovery and indexing

Status: done

Acceptance:
- Walk any GitHub repo directory to find SKILL.md files at arbitrary depth
- Parse YAML frontmatter and Markdown body into structured skill records
- Persist skill records in SQLite with UTC timestamps and audit trail
- POST /api/v1/skills/index accepts a local repo path and returns discovered skill count
- GET /api/v1/skills lists indexed skills with pagination

Implementation: `backend/app/services/discovery.py`, `backend/app/services/parser.py`, `backend/app/models/skill.py`, `backend/app/services/indexer.py`

Tests: `backend/tests/test_discovery.py`, `backend/tests/test_parser.py`, `backend/tests/test_indexer.py`

### semantic-search — TF-IDF semantic search engine

Status: done

Acceptance:
- Build TF-IDF vectors from skill title, description, tags, scope, and body
- Tokenize with stop-word filtering and domain keyword expansion
- GET /api/v1/skills/search?q= returns ranked results by cosine similarity
- Search works fully offline with no LLM key
- Determinism: same query and index always produce same ranking

Implementation: `backend/app/services/search.py`

Tests: `backend/tests/test_search.py`

### skill-explorer-ui — React skill explorer dashboard

Status: done

Acceptance:
- Search box triggers API search and displays ranked results
- Skill list shows all indexed skills with title, scope, description
- Loading, error, and empty states are handled
- Index form allows re-indexing a repo path
- All displayed data comes from the backend API

Implementation: `frontend/src/api/client.ts`, `frontend/src/App.tsx`, `frontend/src/components/SkillSearch.tsx`, `frontend/src/components/SkillList.tsx`, `frontend/src/components/SkillCard.tsx`, `frontend/src/components/Indexer.tsx`

Tests: `frontend/src/__tests__/App.test.tsx`, `frontend/src/__tests__/SkillSearch.test.tsx`, `frontend/src/__tests__/SkillCard.test.tsx`, `frontend/src/__tests__/Indexer.test.tsx`

### skill-quality-metrics — Deterministic skill quality assessment

Status: done

Acceptance:
- Compute completeness, description length, tag count, body word count, and overall score
- GET /api/v1/metrics returns sorted quality metrics for all indexed skills
- Metrics are deterministic and data-driven (no LLM)
- Low-quality skills can be identified and filtered

Implementation: `backend/app/services/quality.py`

Tests: `backend/tests/test_quality.py`

### auth-oidc — Keycloak OIDC authorization-code login

Status: planned

Acceptance:
- SPA PKCE client with access tokens kept in memory
- Backend validates issuer, audience, and signature via JWT
- Viewer/operator/admin role-based authorization on data endpoints
- Explicit logout and CSRF protection on cookie-authenticated writes
- Unauthenticated requests rejected, role denial enforced
- Local demo mode bound to localhost with production refusal

### llm-integration — Optional LLM advisory explanations

Status: planned

Acceptance:
- LLM_API_KEY is the only credential variable; provider/model/base-url configurable
- OpenAI-compatible, Anthropic, Gemini, and Ollama adapters via httpx
- Explanations are opt-in, labeled advisory, grounded in actual skill records
- Provider errors are redacted and never fabricated as successful responses
- Keys only server-side, bounded timeouts

### skill-install — Skill installation and preview

Status: planned

Acceptance:
- Preview skill content before installing
- Download and install skill by scoped identifier
- Conflict detection and resolution
- Export installed skills as a manifest

