import { useState } from "react";
import { SkillSearchHit, SkillSearchResponse } from "../api/client";
import { SkillCard } from "./SkillCard";

interface SkillSearchProps {
  onSearch: (query: string) => Promise<void>;
  loading: boolean;
  response: SkillSearchResponse | null;
}

export function SkillSearch({ onSearch, loading, response }: SkillSearchProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <section>
      <form className="form-row" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="What do you need to do? e.g. 'monetization ads', 'r8 optimization'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn" disabled={loading || !query.trim()}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {!response && !loading && (
        <div className="empty card">
          Enter a natural language query to find skills by what they do, not just by name.
        </div>
      )}

      {loading && <div className="loading card">Searching skills…</div>}

      {response && response.total > 0 && (
        <div>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
            {response.total} result{response.total !== 1 ? "s" : ""} for "{response.query}"
          </p>
          {response.hits.map((hit) => (
            <SkillCard key={hit.id} hit={hit} />
          ))}
        </div>
      )}

      {response && response.total === 0 && !loading && (
        <div className="empty card">
          No skills matched your query. Try a different description.
        </div>
      )}
    </section>
  );
}