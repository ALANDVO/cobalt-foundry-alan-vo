import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { Indexer } from "../components/Indexer";

describe("Indexer", () => {
  it("renders input and button", () => {
    const onIndex = vi.fn();
    render(<Indexer onIndex={onIndex} loading={false} result={null} />);

    expect(
      screen.getByPlaceholderText(/e.g. \/path\/to\/skills-repo/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Index" })).toBeInTheDocument();
  });

  it("calls onIndex with path on submit", async () => {
    const onIndex = vi.fn();
    render(<Indexer onIndex={onIndex} loading={false} result={null} />);

    const input = screen.getByPlaceholderText(/e.g. \/path\/to\/skills-repo/);
    await userEvent.type(input, "/some/repo/path{enter}");

    expect(onIndex).toHaveBeenCalledWith("/some/repo/path");
  });

  it("disables button while loading", () => {
    const onIndex = vi.fn();
    render(<Indexer onIndex={onIndex} loading={true} result={null} />);

    expect(screen.getByRole("button", { name: "Indexing..." })).toBeDisabled();
  });

  it("disables button when input is empty", () => {
    const onIndex = vi.fn();
    render(<Indexer onIndex={onIndex} loading={false} result={null} />);

    expect(screen.getByRole("button", { name: "Index" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Index" })).toHaveAttribute(
      "disabled",
    );
  });

  it("shows index result stats", () => {
    const onIndex = vi.fn();
    render(
      <Indexer
        onIndex={onIndex}
        loading={false}
        result={{ repo_path: "/repo", discovered: 5, indexed: 4, skills: ["a/b"] }}
      />,
    );

    expect(screen.getByText("Discovered: 5")).toBeInTheDocument();
    expect(screen.getByText("Indexed: 4")).toBeInTheDocument();
  });
});