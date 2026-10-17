import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { SkillSearch } from "../components/SkillSearch";
import { SkillSearchResponse } from "../api/client";

const mockResponse: SkillSearchResponse = {
  query: "monetization",
  total: 2,
  hits: [
    {
      id: "ads/admob-integration",
      name: "admob-integration",
      scope: "ads",
      title: "AdMob Ads SDK Integration",
      description: "Integrate Google Mobile Ads SDK.",
      score: 0.95,
      source_path: "ads/admob/SKILL.md",
    },
    {
      id: "performance/r8-analyzer",
      name: "r8-analyzer",
      scope: "performance",
      title: "R8 Optimization Analyzer",
      description: "Analyze R8 optimization decisions.",
      score: 0.30,
      source_path: "performance/r8-analyzer/SKILL.md",
    },
  ],
};

describe("SkillSearch", () => {
  it("renders search input and placeholder", () => {
    const onSearch = vi.fn();
    render(<SkillSearch onSearch={onSearch} loading={false} response={null} />);

    expect(
      screen.getByPlaceholderText(/What do you need to do/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Enter a natural language query/),
    ).toBeInTheDocument();
  });

  it("calls onSearch with query on form submit", async () => {
    const onSearch = vi.fn();
    render(<SkillSearch onSearch={onSearch} loading={false} response={null} />);

    const input = screen.getByPlaceholderText(/What do you need to do/);
    await userEvent.type(input, "ads monetization{enter}");

    expect(onSearch).toHaveBeenCalledWith("ads monetization");
  });

  it("displays search results with scores", async () => {
    const onSearch = vi.fn();
    render(
      <SkillSearch onSearch={onSearch} loading={false} response={mockResponse} />,
    );

    expect(screen.getByText('2 results for "monetization"')).toBeInTheDocument();
    expect(screen.getByText("AdMob Ads SDK Integration")).toBeInTheDocument();
    expect(screen.getByText("R8 Optimization Analyzer")).toBeInTheDocument();
    expect(screen.getByText(/Relevance: 0\.95/)).toBeInTheDocument();
    expect(screen.getByText(/Relevance: 0\.30/)).toBeInTheDocument();
  });

  it("shows empty state when no results", () => {
    const onSearch = vi.fn();
    render(
      <SkillSearch
        onSearch={onSearch}
        loading={false}
        response={{ query: "xyz", total: 0, hits: [] }}
      />,
    );

    expect(screen.getByText(/No skills matched/)).toBeInTheDocument();
  });

  it("shows loading state while searching", () => {
    const onSearch = vi.fn();
    render(<SkillSearch onSearch={onSearch} loading={true} response={null} />);

    expect(screen.getByText("Searching skills…")).toBeInTheDocument();
  });
});