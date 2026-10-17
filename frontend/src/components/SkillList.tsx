import { Skill } from "../api/client";
import { SkillCard } from "./SkillCard";

interface SkillListProps {
  skills: Skill[];
  loading: boolean;
  onEmpty: () => string;
}

export function SkillList({ skills, loading, onEmpty }: SkillListProps) {
  if (loading) {
    return <div className="loading card">Loading skills…</div>;
  }

  if (skills.length === 0) {
    return <div className="empty card">{onEmpty()}</div>;
  }

  // Convert Skill objects to SkillSearchHit format for the SkillCard component
  const hits = skills.map((s) => ({
    id: s.id,
    name: s.name,
    scope: s.scope,
    title: s.title,
    description: s.description,
    score: 1.0,
    source_path: s.source_path,
  }));

  return (
    <div>
      <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
        {skills.length} skill{skills.length !== 1 ? "s" : ""} indexed
      </p>
      {hits.map((hit) => (
        <SkillCard key={hit.id} hit={hit} showScore={false} />
      ))}
    </div>
  );
}