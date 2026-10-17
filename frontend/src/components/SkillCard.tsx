import { SkillSearchHit } from "../api/client";

interface SkillCardProps {
  hit: SkillSearchHit;
  showScore?: boolean;
}

const SCOPE_BADGE_CLASS: Record<string, string> = {
  performance: "badge-performance",
  ads: "badge-ads",
  lint: "badge-lint",
  devtools: "badge-devtools",
};

export function SkillCard({ hit, showScore = true }: SkillCardProps) {
  const badgeClass = SCOPE_BADGE_CLASS[hit.scope] || "badge-default";

  return (
    <article className="card">
      <div className="skill-meta">
        <span className={`badge ${badgeClass}`}>{hit.scope}</span>
        <span className="name">{hit.name}</span>
        {showScore && <span className="score">Relevance: {hit.score.toFixed(2)}</span>}
      </div>
      <h3 className="skill-title">{hit.title}</h3>
      {hit.description && (
        <p className="skill-description">{hit.description}</p>
      )}
      {!hit.description && (
        <p className="skill-description" style={{ fontStyle: "italic", opacity: 0.6 }}>
          No description available.
        </p>
      )}
      <div className="skill-tags">
        {hit.source_path && (
          <span className="tag" style={{ fontSize: "0.65rem" }}>
            {hit.source_path}
          </span>
        )}
      </div>
    </article>
  );
}