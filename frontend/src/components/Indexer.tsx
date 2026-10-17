import { useState } from "react";
import { IndexResult } from "../api/client";

interface IndexerProps {
  onIndex: (repoPath: string) => Promise<void>;
  loading: boolean;
  result: IndexResult | null;
}

export function Indexer({ onIndex, loading, result }: IndexerProps) {
  const [repoPath, setRepoPath] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath.trim()) return;
    await onIndex(repoPath.trim());
  };

  return (
    <section className="card">
      <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
        Index a Skills Repository
      </h2>
      <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginBottom: "0.75rem" }}>
        Point Cobalt Foundry at a local clone of a GitHub CLI skills repository
        to discover SKILL.md files at any depth, regardless of directory layout.
      </p>
      <form className="form-row" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="e.g. /path/to/skills-repo or ./sample-repo"
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="btn" disabled={loading || !repoPath.trim()}>
          {loading ? "Indexing..." : "Index"}
        </button>
      </form>
      {result && (
        <div className="stats">
          <span className="stat">Discovered: {result.discovered}</span>
          <span className="stat">Indexed: {result.indexed}</span>
        </div>
      )}
    </section>
  );
}