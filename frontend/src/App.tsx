import { useEffect, useState } from "react";
import { api, HealthResponse, IndexResult, Skill, SkillSearchResponse } from "./api/client";
import { Indexer } from "./components/Indexer";
import { SkillList } from "./components/SkillList";
import { SkillSearch } from "./components/SkillSearch";

type View = "search" | "list";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("search");
  const [searchResponse, setSearchResponse] = useState<SkillSearchResponse | null>(null);
  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [allSkillsLoading, setAllSkillsLoading] = useState(false);
  const [lastIndex, setLastIndex] = useState<IndexResult | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  const loadAllSkills = async () => {
    setAllSkillsLoading(true);
    setError(null);
    try {
      const skills = await api.listSkills();
      setAllSkills(skills);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load skills");
    } finally {
      setAllSkillsLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await api.search(query);
      setSearchResponse(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setSearchResponse(null);
    } finally {
      setLoading(false);
    }
  };

  const handleIndex = async (repoPath: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.indexRepo(repoPath);
      setLastIndex(result);
      // Reload skills after indexing
      await loadAllSkills();
      // Switch to list view to show indexed skills
      setView("list");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Indexing failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div>
          <h1>Cobalt Foundry</h1>
          <div className="subtitle">Skill discovery &amp; semantic search</div>
        </div>
        {health && (
          <div className="subtitle">
            v{health.version} · {health.status}
          </div>
        )}
      </header>

      {error && <div className="error card">{error}</div>}

      <Indexer onIndex={handleIndex} loading={loading} result={lastIndex} />

      <div className="form-row" style={{ marginBottom: "1.5rem" }}>
        <button
          className="btn"
          style={{
            background: view === "search" ? "var(--accent)" : "var(--surface-2)",
            color: view === "search" ? "#000" : "var(--text)",
          }}
          onClick={() => { setView("search"); setSearchResponse(null); }}
        >
          Search
        </button>
        <button
          className="btn"
          style={{
            background: view === "list" ? "var(--accent)" : "var(--surface-2)",
            color: view === "list" ? "#000" : "var(--text)",
          }}
          onClick={() => { setView("list"); loadAllSkills(); }}
        >
          All Skills ({allSkills.length})
        </button>
      </div>

      {view === "search" ? (
        <SkillSearch
          onSearch={handleSearch}
          loading={loading}
          response={searchResponse}
        />
      ) : (
        <SkillList
          skills={allSkills}
          loading={allSkillsLoading}
          onEmpty={() => {
            if (!lastIndex) {
              return "No skills indexed yet. Use the form above to index a repository.";
            }
            return "No skills found.";
          }}
        />
      )}
    </div>
  );
}