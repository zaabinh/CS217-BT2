import { beforeAll, describe, expect, it } from "vitest";
import { ApiError, solve, type SolveRequest } from "./api";
import { visualState } from "./geometry";
import { VARIABLES, type Variable } from "./variables";

// Real FastAPI backend, no mocks. Start it first (see README) or set BACKEND_URL.
const BASE = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

beforeAll(async () => {
  const res = await fetch(`${BASE}/api/v1/variables`).catch(() => null);
  if (!res?.ok) throw new Error(`Backend not reachable at ${BASE}; start uvicorn first.`);
});

describe("frontend API client against the real backend", () => {
  it("solves the 3-4-5 triangle", async () => {
    const r = await solve({ facts: { a: 3, b: 4, c: 5 }, goals: ["S", "hc", "R"] }, undefined, BASE);
    expect(r.status).toBe("SOLVED");
    expect(r.reason_code).toBe("GOALS_REACHED");
    expect(r.stats?.steps).toBe(r.trace.length);
    expect(r.facts.S).toBeCloseTo(6);
    expect(r.facts.hc).toBeCloseTo(2.4);
    expect(r.facts.R).toBeCloseTo(2.5);
    expect(r.trace.length).toBeGreaterThan(0);
    expect(r.trace[0]).toMatchObject({ step: 1, rule_id: expect.stringMatching(/^R\d\d$/), group: expect.stringMatching(/^Q\d\d$/) });
    expect(visualState(r, false).kind).toBe("constructed");
  });

  it("solves SAS (b=3, c=4, A=90)", async () => {
    const r = await solve({ facts: { b: 3, c: 4, A: 90 }, goals: ["a", "S"] }, undefined, BASE);
    expect(r.status).toBe("SOLVED");
    expect(r.facts.a).toBeCloseTo(5);
    expect(r.facts.S).toBeCloseTo(6);
  });

  it("calculates everything derivable with all 13 goals", async () => {
    const r = await solve({ facts: { A: 50, B: 60, c: 10 }, goals: [...VARIABLES] }, undefined, BASE);
    expect(r.status).toBe("SOLVED");
    expect(Object.keys(r.facts)).toHaveLength(13);
  });

  it("reports insufficient information as UNRESOLVED without geometry", async () => {
    const r = await solve({ facts: { a: 3 }, goals: ["S"] }, undefined, BASE);
    expect(r.status).toBe("UNRESOLVED");
    expect(r.missing).toEqual(["S"]);
    expect(visualState(r, false).kind).toBe("placeholder");
  });

  it("reports an impossible triangle as INVALID", async () => {
    const r = await solve({ facts: { a: 1, b: 2, c: 3 }, goals: ["S"] }, undefined, BASE);
    expect(r.status).toBe("INVALID");
    expect(r.message).toMatch(/Triangle inequality/);
    expect(visualState(r, false).kind).toBe("invalid");
  });

  it("reports conflicting facts as INCONSISTENT", async () => {
    const r = await solve({ facts: { a: 3, b: 4, c: 5, S: 7 }, goals: ["S"] }, undefined, BASE);
    expect(r.status).toBe("INCONSISTENT");
    expect(r.message).toMatch(/R20/);
  });

  it("recognizes SSA as ambiguous", async () => {
    const r = await solve({ facts: { a: 3, b: 4, A: 30 }, goals: ["c"] }, undefined, BASE);
    expect(r.status).toBe("UNRESOLVED");
    expect(visualState(r, false).kind).toBe("ambiguous");
  });

  it("surfaces schema rejections (HTTP 422) as ApiError", async () => {
    const bad = { facts: { x: 1 }, goals: ["S"] } as unknown as SolveRequest;
    const error = await solve(bad, undefined, BASE).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    const empty = await solve({ facts: {}, goals: [] as Variable[] }, undefined, BASE).catch((e) => e);
    expect(empty.status).toBe(422);
  });

  it("surfaces an unreachable server as a network error", async () => {
    await expect(solve({ facts: {}, goals: ["S"] }, undefined, "http://127.0.0.1:9")).rejects.toMatchObject({ kind: "network" });
  });
});
