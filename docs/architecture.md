# Architecture

## Overview

Cobalt Foundry is a two-service application: a FastAPI backend with SQLite
persistence and a React/Vite frontend served by nginx.

## Backend Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│  /health │ /index   │ /search  │ /skills  │ /metrics │
│  /audit  │          │          │          │          │
├──────────┴──────────┴──────────┴──────────┴──────────┤
│                    Dependency Injection               │
│  get_db (SQLAlchemy Session)                          │
│  get_indexer (SkillIndexer per request)               │
├─────────────────────────────────────────────────────┤
│                     Core Services                     │
│  discovery.py  → walks repo, finds SKILL.md           │
│  parser.py     → parses YAML frontmatter + body       │
│  search.py     → TF-IDF engine with keyword expansion  │
│  quality.py    → deterministic quality metrics         │
│  indexer.py    → orchestrates discovery → parse → DB  │
├─────────────────────────────────────────────────────┤
│                    Data Layer                         │
│  models/skill.py    → Skill, AuditLog ORM models      │
│  schemas/skill.py   → Pydantic response schemas        │
│  core/database.py   → engine, session, UTCDateTime     │
└─────────────────────────────────────────────────────┘
```

### Request Lifecycle

1. POST `/skills/index` with `{repo_path}` → `SkillIndexer.index_repo()`:
   - `discover_skills()` walks the filesystem for `SKILL.md` files
   - `parse_skill_md()` extracts metadata per file
   - Each parsed skill is upserted into SQLite
   - `AuditLog` entry is stored
   - `commit()` persists the transaction
   - TF-IDF search index is rebuilt from the database
2. GET `/skills/search?q=...` → `indexer.search_index.search()`:
   - If the in-memory TF-IDF index is empty, it is rebuilt from the DB
   - Query is tokenized, expanded with domain keywords, and scored
   - Results are ranked by cosine similarity and returned
3. GET `/skills` / GET `/skills/{id}` → direct SQLAlchemy queries

### TF-IDF Algorithm

The search engine (`services/search.py`) uses:

- **Tokenisation**: lowercase, alphanumeric extraction, stop-word filtering
- **Keyword expansion**: Android-specific synonyms (e.g., "r8" → "optimization")
- **TF-IDF weighting**: term frequency × smoothed inverse document frequency
- **Cosine similarity**: normalized dot product of query and document vectors
- **Field weighting**: title ×3, description ×2, tags ×2, scope ×2, body ×1

The algorithm is fully deterministic — the same index and query always produce
the same ranking. No LLM key is required.

### Quality Metrics

`services/quality.py` computes per-skill metrics:

- **Completeness**: fraction of optional fields present (0.0–1.0)
- **Description length**: character count
- **Tag count**: number of tags
- **Body word count**: number of words in the Markdown body
- **Overall score**: weighted geometric mean of normalised sub-scores

These metrics are purely data-driven and deterministic.

## Frontend Architecture

```
┌─────────────────────────────────────────────────────┐
│              React + Vite (SPA)                       │
├─────────────────────────────────────────────────────┤
│  src/                                                │
│    api/client.ts      → typed fetch wrapper          │
│    main.tsx           → React entry point             │
│    App.tsx            → state + routing               │
│    components/                                          │
│      Indexer.tsx      → repo path form                │
│      SkillSearch.tsx  → search input + results        │
│      SkillList.tsx    → all-skills grid                │
│      SkillCard.tsx    → individual skill display       │
└─────────────────────────────────────────────────────┘
```

The frontend uses no build-time API client generator — `api/client.ts` is
hand-written and typed to match the backend Pydantic schemas. All displayed
values come from the API at runtime.

## Planned Additions (Round 2+)

- **Keycloak OIDC**: Authorization-code flow with state + nonce + PKCE
- **Bearer-only API**: Access tokens kept in memory, never in localStorage
- **Role-based access**: Viewer / operator / admin roles
- **LLM adapter**: Optional advisory explanations via server-side API key