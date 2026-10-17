import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, afterEach } from "vitest";
import App from "../App";
import { api } from "../api/client";

const mockHealth = { status: "ok", version: "1.0.0" };

const mockSkills = [
  {
    id: "performance/r8-analyzer",
    name: "r8-analyzer",
    scope: "performance",
    title: "R8 Optimization Analyzer",
    description: "Analyze R8 optimization decisions.",
    tags: ["android", "r8"],
    body: "# R8 Analyzer",
    source_path: "performance/r8-analyzer/SKILL.md",
    repo_path: "/repo",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "ads/admob-integration",
    name: "admob-integration",
    scope: "ads",
    title: "AdMob Ads SDK Integration",
    description: "Integrate Google Mobile Ads SDK.",
    tags: ["android", "ads", "admob"],
    body: "# AdMob",
    source_path: "ads/admob/SKILL.md",
    repo_path: "/repo",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders with health check version", async () => {
    vi.spyOn(api, "health").mockResolvedValue(mockHealth);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Cobalt Foundry")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument();
    });
  });

  it("displays indexed skills in list view", async () => {
    vi.spyOn(api, "health").mockResolvedValue(mockHealth);
    vi.spyOn(api, "listSkills").mockResolvedValue(mockSkills);

    render(<App />);

    await waitFor(() => screen.getByRole("button", { name: /All Skills/ }));
    await userEvent.click(screen.getByRole("button", { name: /All Skills/ }));

    await waitFor(() => {
      expect(screen.getByText("R8 Optimization Analyzer")).toBeInTheDocument();
    });
  });

  it("search results appear after search", async () => {
    vi.spyOn(api, "health").mockResolvedValue(mockHealth);
    vi.spyOn(api, "search").mockResolvedValue({
      query: "r8",
      total: 1,
      hits: [{
        id: "performance/r8-analyzer",
        name: "r8-analyzer",
        scope: "performance",
        title: "R8 Optimization Analyzer",
        description: "Analyze R8 optimization decisions.",
        score: 0.92,
        source_path: "performance/r8-analyzer/SKILL.md",
      }],
    });

    render(<App />);

    const input = await screen.findByPlaceholderText(/What do you need to do/);
    await userEvent.type(input, "r8");
    await userEvent.keyboard("{enter}");

    await waitFor(() => {
      expect(screen.getByText("R8 Optimization Analyzer")).toBeInTheDocument();
    });
  });

  it("shows error when indexing fails", async () => {
    vi.spyOn(api, "health").mockResolvedValue(mockHealth);
    vi.spyOn(api, "listSkills").mockResolvedValue([]);
    vi.spyOn(api, "indexRepo").mockRejectedValue(new Error("Indexing failed"));

    render(<App />);

    const input = await screen.findByPlaceholderText(/e.g. \/path\/to\/skills-repo/);
    await userEvent.type(input, "/bad/path");
    await userEvent.keyboard("{enter}");

    await waitFor(() => {
      expect(screen.getByText("Indexing failed")).toBeInTheDocument();
    });
  });
});