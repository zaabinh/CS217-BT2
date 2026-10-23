import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { ApiError, type SolveRequest, type SolveResponse } from "./lib/api";

const solved345: SolveResponse = {
  status: "SOLVED",
  facts: { a: 3, b: 4, c: 5, p: 6, S: 6.000000000000001, hc: 2.4 },
  missing: [],
  trace: [
    { step: 1, rule_id: "R04", group: "Q02", inputs: { a: 3, b: 4, c: 5 }, output: "p", value: 6, formula: "p = (a + b + c) / 2" },
    { step: 2, rule_id: "R20", group: "Q05", inputs: { p: 6, a: 3, b: 4, c: 5 }, output: "S", value: 6.000000000000001, formula: "S = sqrt(p*(p-a)*(p-b)*(p-c))" },
    { step: 3, rule_id: "R28", group: "Q06", inputs: { S: 6, c: 5 }, output: "hc", value: 2.4, formula: "hc = 2*S/c" },
  ],
  message: "All goals derived and facts passed validation",
};

function setup(solve = vi.fn(async (_: SolveRequest) => solved345)) {
  const user = userEvent.setup();
  render(<App solve={solve} />);
  const type = async (v: string, value: string) => {
    const input = document.getElementById(`input-${v}`) as HTMLInputElement;
    await user.clear(input);
    if (value) await user.type(input, value);
  };
  const target = (name: string) => screen.getByRole("button", { name: `Find ${name}` });
  return { user, solve, type, target };
}

async function solve345(s: ReturnType<typeof setup>) {
  await s.type("a", "3"); await s.type("b", "4"); await s.type("c", "5");
  await s.user.click(s.target("Area"));
  await s.user.click(s.target("Altitude to c"));
  await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
  await screen.findByTestId("status-badge");
}

describe("App", () => {
  it("shows contextual validation and blocks solving invalid input", async () => {
    const s = setup();
    await s.user.click(s.target("Area"));
    await s.type("a", "-2");
    expect(screen.getByText("Side lengths must be greater than zero.")).toBeInTheDocument();
    expect(document.getElementById("input-a")).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("button", { name: "Solve selected" })).toBeDisabled();
    await s.type("A", "190");
    expect(screen.getByText("Angles must be between 0° and 180°.")).toBeInTheDocument();
    await s.type("a", "2"); await s.type("A", "");
    expect(screen.getByRole("button", { name: "Solve selected" })).toBeEnabled();
  });

  it("keeps advanced parameters collapsed until opened", async () => {
    const s = setup();
    expect(document.getElementById("input-S")).toBeNull();
    await s.user.click(screen.getByRole("button", { name: /Advanced parameters/ }));
    expect(document.getElementById("input-S")).toBeInTheDocument();
    await s.type("S", "6");
    expect(screen.getByText("(1 entered)")).toBeInTheDocument();
  });

  it("toggles target chips, select all and clear", async () => {
    const s = setup();
    const solveBtn = screen.getByRole("button", { name: "Solve selected" });
    expect(solveBtn).toBeDisabled();
    await s.user.click(s.target("Area"));
    expect(s.target("Area")).toHaveAttribute("aria-pressed", "true");
    expect(solveBtn).toBeEnabled();
    await s.user.click(s.target("Area"));
    expect(s.target("Area")).toHaveAttribute("aria-pressed", "false");
    await s.user.click(screen.getByRole("button", { name: "Select all" }));
    expect(within(screen.getByRole("group", { name: "Target parameters" })).getAllByRole("button", { pressed: true })).toHaveLength(13);
    await s.user.click(screen.getByRole("button", { name: "Clear" }));
    expect(solveBtn).toBeDisabled();
  });

  it("sends only populated facts and selected goals, then renders results", async () => {
    const s = setup();
    await solve345(s);
    expect(s.solve).toHaveBeenCalledTimes(1);
    expect(s.solve.mock.calls[0][0]).toEqual({ facts: { a: 3, b: 4, c: 5 }, goals: ["hc", "S"] });
    expect(screen.getByTestId("status-badge")).toHaveTextContent("SOLVED");
    expect(screen.getByTestId("value-S")).toHaveTextContent("6");
    expect(screen.getByTestId("value-hc")).toHaveTextContent("2.4");
    expect(within(screen.getByTestId("result-S")).getByText("Inferred")).toBeInTheDocument();
    expect(screen.getByTestId("triangle-svg")).toBeInTheDocument();
  });

  it("does not write inferred values into the input fields", async () => {
    const s = setup();
    await solve345(s);
    await s.user.click(screen.getByRole("button", { name: /Advanced parameters/ }));
    expect(document.getElementById("input-S")).toHaveValue("");
  });

  it("Calculate all possible requests every variable", async () => {
    const s = setup();
    await s.type("a", "3");
    await s.user.click(screen.getByRole("button", { name: "Calculate all possible" }));
    await screen.findByTestId("status-badge");
    expect(s.solve.mock.calls[0][0].goals).toHaveLength(13);
  });

  it("shows loading and prevents duplicate submissions", async () => {
    let resolve!: (r: SolveResponse) => void;
    const s = setup(vi.fn(() => new Promise<SolveResponse>((r) => { resolve = r; })));
    await s.type("a", "3");
    await s.user.click(s.target("Area"));
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    expect(screen.getByRole("button", { name: "Solve selected" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Calculate all possible" })).toBeDisabled();
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    expect(s.solve).toHaveBeenCalledTimes(1);
    resolve({ ...solved345, status: "UNRESOLVED", facts: { a: 3 }, missing: ["S"], trace: [] });
    expect(await screen.findByTestId("status-badge")).toHaveTextContent("UNRESOLVED");
    expect(screen.getByTestId("value-S")).toHaveTextContent("—");
    expect(screen.getByText("Enter sufficient parameters to construct a triangle.")).toBeInTheDocument();
  });

  it("ignores a slower, older response", async () => {
    const pending: ((r: SolveResponse) => void)[] = [];
    const s = setup(vi.fn(() => new Promise<SolveResponse>((r) => pending.push(r))));
    await s.type("a", "3");
    await s.user.click(s.target("Area"));
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    // Reset aborts the first request, then a second one is sent.
    await s.user.click(screen.getByRole("button", { name: "Reset" }));
    await s.type("a", "3"); await s.type("b", "4"); await s.type("c", "5");
    await s.user.click(s.target("Area"));
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    pending[1](solved345);
    await screen.findByTestId("status-badge");
    pending[0]({ ...solved345, status: "INVALID", message: "old" });
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.getByTestId("status-badge")).toHaveTextContent("SOLVED");
  });

  it("marks results stale when a fact changes", async () => {
    const s = setup();
    await solve345(s);
    expect(screen.queryByTestId("stale-banner")).toBeNull();
    await s.type("a", "3.5");
    expect(screen.getByTestId("stale-banner")).toBeInTheDocument();
    expect(screen.queryByTestId("triangle-svg")).toBeNull();
    expect(screen.getByText("Inputs changed. Solve again to update the triangle.")).toBeInTheDocument();
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    await waitFor(() => expect(screen.queryByTestId("stale-banner")).toBeNull());
  });

  it("shows API errors with a retry action", async () => {
    const solve = vi.fn()
      .mockRejectedValueOnce(new ApiError("Cannot reach the solver backend.", "network"))
      .mockResolvedValueOnce(solved345);
    const s = setup(solve);
    await s.type("a", "3");
    await s.user.click(s.target("Area"));
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach the solver backend.");
    await s.user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByTestId("status-badge")).toHaveTextContent("SOLVED");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("presents INVALID and INCONSISTENT without values or success", async () => {
    const s = setup(vi.fn(async () => ({ status: "INCONSISTENT", facts: { a: 3, b: 4, c: 5, S: 7 }, missing: [], trace: [], message: "Q05/R20 Heron: S=7, expected 6.000000000000001" }) as SolveResponse));
    await s.type("a", "3");
    await s.user.click(s.target("Area"));
    await s.user.click(screen.getByRole("button", { name: "Solve selected" }));
    expect(await screen.findByTestId("status-badge")).toHaveTextContent("INCONSISTENT");
    expect(screen.queryByText("Solved")).toBeNull();
    expect(screen.queryByTestId("result-S")).toBeNull();
    expect(screen.getByText(/Q05\/R20 Heron/)).toBeInTheDocument();
    expect(screen.queryByTestId("triangle-svg")).toBeNull();
  });

  it("expands solution steps and filters them for a selected result", async () => {
    const s = setup();
    await solve345(s);
    expect(screen.queryByTestId("step-1")).toBeNull();
    await s.user.click(screen.getByRole("button", { name: /Solution steps/ }));
    expect(screen.getByTestId("step-3")).toHaveTextContent("hc = 2·S/c");
    await s.user.click(screen.getByRole("button", { name: /Solution steps/ }));
    await s.user.click(screen.getByTestId("result-S"));
    expect(screen.getByTestId("result-S")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByTestId("step-2")).toBeInTheDocument();
    expect(screen.queryByTestId("step-3")).toBeNull();
    expect(screen.getByTestId("triangle-area")).toHaveClass("fill-primary/15");
    await s.user.click(screen.getByRole("button", { name: "Full trace" }));
    expect(screen.getByTestId("step-3")).toBeInTheDocument();
    await s.user.click(screen.getByTestId("step-3"));
    expect(screen.getByTestId("altitude-hc")).toBeInTheDocument();
    expect(screen.getByTestId("side-c")).toHaveAttribute("data-highlight", "secondary");
  });

  it("loads an example without solving", async () => {
    const s = setup();
    await s.user.selectOptions(screen.getByLabelText("Load an example problem"), "sas");
    expect(document.getElementById("input-b")).toHaveValue("3");
    expect(document.getElementById("input-c")).toHaveValue("4");
    expect(document.getElementById("input-A")).toHaveValue("90");
    expect(s.target("Side a")).toHaveAttribute("aria-pressed", "true");
    expect(s.solve).not.toHaveBeenCalled();
  });

  it("resets the workspace", async () => {
    const s = setup();
    await solve345(s);
    await s.user.click(screen.getByRole("button", { name: "Reset" }));
    expect(document.getElementById("input-a")).toHaveValue("");
    expect(screen.queryByTestId("status-badge")).toBeNull();
    expect(s.target("Area")).toHaveAttribute("aria-pressed", "false");
  });
});
