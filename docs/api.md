# API Reference

All endpoints are under `/api/v1/`.

## `GET /health`

Returns application health and version.

**Response:**
```json
{"status": "ok", "version": "1.0.0"}
```

## `POST /skills/index`

Discover and index all `SKILL.md` files under the given repository path.

**Request body:**
```json
{"repo_path": "/path/to/skills-repo"}
```

**Response (201):**
```json
{
  "repo_path": "/path/to/skills-repo",
  "discovered": 4,
  "indexed": 4,
  "skills": ["performance/r8-analyzer", "ads/admob-integration"]
}
```

**Errors:**
- `404` — Repository path not found
- `403` — Permission denied
- `422` — Validation error (missing `repo_path`)

## `GET /skills`

List all indexed skills with optional filtering and pagination.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `scope` | string | no | — | Filter by scope |
| `skip` | int | no | 0 | Number of records to skip |
| `limit` | int | no | 50 | Max records (1–200) |

**Response:**
```json
[{"id": "performance/r8-analyzer", "name": "r8-analyzer", "...": "..."}]
```

## `GET /skills/search?q=<query>`

Semantic search for skills matching a natural-language query.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `q` | string | yes | — | Search query (1–256 chars) |
| `top_k` | int | no | 20 | Max results (1–100) |

**Response:**
```json
{
  "query": "optimiz",
  "total": 1,
  "hits": [{"id": "perf:r8", "name": "r8-analyzer", "score": 0.92, "...": "..."}]
}
```

## `GET /skills/{skill_id}`

Retrieve a single skill by its identifier (`scope/name`). The `skill_id` path
parameter accepts slashes (e.g., `performance/r8-analyzer`).

**Response:**
```json
{"id": "performance/r8-analyzer", "name": "r8-analyzer", "...": "..."}
```

**Errors:**
- `404` — Skill not found

## `GET /metrics`

Compute quality metrics for all indexed skills.

**Response:**
```json
{
  "total": 4,
  "metrics": [{"skill_id": "perf:r8", "completeness": 1.0, "overall_score": 0.85, "...": "..."}]
}
```

Metrics are sorted by `overall_score` descending.

## `GET /audit-log`

Return recent audit-log entries.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `limit` | int | no | 50 | Max entries (1–200) |

**Response:**
```json
[{"id": 1, "action": "index_repo", "detail": "{...}", "created_at": "..."}]
```