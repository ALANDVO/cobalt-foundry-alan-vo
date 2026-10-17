import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SkillCard } from "../components/SkillCard";
import { SkillSearchHit } from "../api/client";

const mockHit: SkillSearchHit = {
  id: "performance/r8-analyzer",
  name: "r8-analyzer",
  scope: "performance",
  title: "R8 Optimization Analyzer",
  description: "Analyze R8 optimization decisions.",
  score: 0.87,
  source_path: "performance/r8-analyzer/SKILL.md",
};

describe("SkillCard", () => {
  it("renders skill metadata, title, and description", () => {
    render(<SkillCard hit={mockHit} />);

    expect(screen.getByText("r8-analyzer")).toBeInTheDocument();
    expect(screen.getByText("R8 Optimization Analyzer")).toBeInTheDocument();
    expect(screen.getByText("Analyze R8 optimization decisions.")).toBeInTheDocument();
  });

  it("shows relevance score when showScore is true (default)", () => {
    render(<SkillCard hit={mockHit} />);
    expect(screen.getByText(/Relevance: 0\.87/)).toBeInTheDocument();
  });

  it("hides score when showScore is false", () => {
    render(<SkillCard hit={mockHit} showScore={false} />);
    expect(screen.queryByText(/Relevance/)).not.toBeInTheDocument();
  });

  it("shows empty description fallback", () => {
    const hit: SkillSearchHit = { ...mockHit, description: null };
    render(<SkillCard hit={hit} showScore={false} />);
    expect(screen.getByText("No description available.")).toBeInTheDocument();
  });
});