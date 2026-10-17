/**
 * Typed API client for the Cobalt Foundry backend.
 *
 * All interfaces are derived from the backend Pydantic schemas
 * (see backend/app/schemas/skill.py).
 */

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// ---- Types (mirror backend schemas) ----

export interface Skill {
  id: string;
  name: string;
  scope: string;
  title: string;
  description: string | null;
  tags: string[];
  body: string | null;
  source_path: string;
  repo_path: string;
  created_at: string;
  updated_at: string;
}

export interface SkillSearchHit {
  id: string;
  name: string;
  scope: string;
  title: string;
  description: string | null;
  score: number;
  source_path: string;
}

export interface SkillSearchResponse {
  query: string;
  total: number;
  hits: SkillSearchHit[];
}

export interface IndexResult {
  repo_path: string;
  discovered: number;
  indexed: number;
  skills: string[];
}

export interface IndexRequest {
  repo_path: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  detail: string;
  created_at: string;
}

// ---- API client ----

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!resp.ok) {
    const msg = await resp.text().catch(() => resp.statusText);
    throw new ApiError(msg || resp.statusText, resp.status);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  health(): Promise<HealthResponse> {
    return fetchJson<HealthResponse>(`${API_BASE}/api/v1/health`);
  },

  indexRepo(repoPath: string): Promise<IndexResult> {
    return fetchJson<IndexResult>(`${API_BASE}/api/v1/skills/index`, {
      method: "POST",
      body: JSON.stringify({ repo_path: repoPath }),
    });
  },

  search(query: string, topK: number = 20): Promise<SkillSearchResponse> {
    return fetchJson<SkillSearchResponse>(
      `${API_BASE}/api/v1/skills/search?q=${encodeURIComponent(query)}&top_k=${topK}`,
    );
  },

  listSkills(
    scope?: string,
    skip: number = 0,
    limit: number = 50,
  ): Promise<Skill[]> {
    const params = new URLSearchParams();
    if (scope) params.set("scope", scope);
    params.set("skip", String(skip));
    params.set("limit", String(limit));
    return fetchJson<Skill[]>(`${API_BASE}/api/v1/skills?${params}`);
  },

  getSkill(id: string): Promise<Skill> {
    return fetchJson<Skill>(`${API_BASE}/api/v1/skills/${encodeURIComponent(id)}`);
  },

  getAuditLog(limit: number = 50): Promise<AuditLogEntry[]> {
    return fetchJson<AuditLogEntry[]>(`${API_BASE}/api/v1/audit-log?limit=${limit}`);
  },
};