import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, solve, type InferenceStep, type SolveResponse } from "./api";
import { formatValue, prettyFormula } from "./format";
import { angleArc, circumcircle, fitLayout, formsTriangle, incircle, isSSA, rawVertices, visualState, dist } from "./geometry";
import { buildFacts, parseField } from "./input";
import { explainMessage, STATUS_UI } from "./status";
import { relevantSteps } from "./trace";

const response = (over: Partial<SolveResponse> = {}): SolveResponse =>
  ({ status: "SOLVED", facts: {}, missing: [], trace: [], message: "ok", ...over });

describe("input parsing and validation", () => {
  it("distinguishes empty, invalid and valid", () => {
    expect(parseField("a", "")).toEqual({ kind: "empty" });
    expect(parseField("a", "   ")).toEqual({ kind: "empty" });
    expect(parseField("a", "abc").kind).toBe("invalid");
    expect(parseField("a", "1.2.3").kind).toBe("invalid");
    expect(parseField("a", "4.5")).toEqual({ kind: "valid", value: 4.5 });
    expect(parseField("a", "4,5")).toEqual({ kind: "valid", value: 4.5 });
    expect(parseField("a", "1e2")).toEqual({ kind: "valid", value: 100 });
    expect(parseField("a", "1e999")).toMatchObject({ kind: "invalid", message: "This number is too large." });
  });

  it("uses contextual messages for sides, angles and other values", () => {
    expect(parseField("b", "0")).toMatchObject({ message: "Side lengths must be greater than zero." });
    expect(parseField("A", "180")).toMatchObject({ message: "Angles must be between 0° and 180°." });
    expect(parseField("A", "0")).toMatchObject({ kind: "invalid" });
    expect(parseField("A", "179.9")).toEqual({ kind: "valid", value: 179.9 });
    expect(parseField("S", "-1")).toMatchObject({ message: "Value must be greater than zero." });
  });

  it("builds facts from populated fields only and refuses invalid input", () => {
    expect(buildFacts({ a: "3", b: "", c: "5" })).toEqual({ a: 3, c: 5 });
    expect(buildFacts({})).toEqual({});
    expect(buildFacts({ a: "3", B: "200" })).toBeNull();
  });

  it("keeps full precision", () => {
    expect(buildFacts({ a: "0.1234567890123" })).toEqual({ a: 0.1234567890123 });
  });
});

describe("formatting", () => {
  it("rounds for display only", () => {
    expect(formatValue(6.000000000000001)).toBe("6");
    expect(formatValue(2.4)).toBe("2.4");
    expect(formatValue(36.86989764584402)).toBe("36.8699");
    expect(formatValue(0.000123456)).toBe("0.0001235");
  });
  it("prettifies formulas", () => {
    expect(prettyFormula("S = sqrt(p*(p-a))")).toBe("S = √(p·(p-a))");
    expect(prettyFormula("A = acos_deg((b^2 + c^2 - a^2)/(2*b*c))")).toBe("A = arccos((b² + c² - a²)/(2·b·c))");
    expect(prettyFormula("a = b*sin_deg(A)/sin_deg(B)")).toBe("a = b·sin(A)/sin(B)");
  });
});

describe("status mapping", () => {
  it("maps every status to a tone", () => {
    expect(STATUS_UI.SOLVED.tone).toBe("success");
    expect(STATUS_UI.UNRESOLVED.tone).toBe("warning");
    expect(STATUS_UI.INVALID.tone).toBe("danger");
    expect(STATUS_UI.INCONSISTENT.tone).toBe("danger");
  });
  it("explains known backend messages", () => {
    expect(explainMessage("INVALID", "Triangle inequality violated (possibly degenerate)")).toMatch(/cannot form a valid triangle/);
    expect(explainMessage("INCONSISTENT", "Q01: A+B+C must equal 180 degrees")).toMatch(/add up to 180°/);
    expect(explainMessage("INCONSISTENT", "Q05/R20 Heron: S=7, expected 6")).toMatch(/contradict/);
    expect(explainMessage("UNRESOLVED", "Goals cannot be derived")).toMatch(/cannot derive/);
  });
});

describe("relevant trace steps", () => {
  const step = (n: number, output: InferenceStep["output"], inputs: string[]): InferenceStep =>
    ({ step: n, rule_id: `R${n}`, group: "Q01", output, value: 1, formula: "", inputs: Object.fromEntries(inputs.map((v) => [v, 1])) });
  const trace = [step(1, "p", ["a", "b", "c"]), step(2, "A", ["a", "b", "c"]), step(3, "S", ["p", "a", "b", "c"]), step(4, "hc", ["S", "c"])];

  it("follows dependencies back to given facts", () => {
    expect(relevantSteps(trace, "hc").map((s) => s.step)).toEqual([1, 3, 4]);
    expect(relevantSteps(trace, "A").map((s) => s.step)).toEqual([2]);
  });
  it("is empty for a given value", () => {
    expect(relevantSteps(trace, "a")).toEqual([]);
  });
});

describe("geometry", () => {
  it("places vertices with correct side lengths", () => {
    const sides = { a: 3, b: 4, c: 5 };
    const { A, B, C } = rawVertices(sides);
    expect(dist(B, C)).toBeCloseTo(3);
    expect(dist(A, C)).toBeCloseTo(4);
    expect(dist(A, B)).toBeCloseTo(5);
  });

  it("handles obtuse triangles", () => {
    const { A, B, C } = rawVertices({ a: 2, b: 2, c: 3.9 });
    expect(dist(A, B)).toBeCloseTo(3.9);
    expect(A.y).toBeGreaterThan(0);
    expect(A.x).toBeGreaterThan(C.x / 2);
    expect(dist(B, C)).toBeCloseTo(2);
  });

  it("fits inside the box with margins and preserves proportions", () => {
    for (const sides of [{ a: 3, b: 4, c: 5 }, { a: 10, b: 5.01, c: 5 }, { a: 1, b: 100, c: 100 }]) {
      const L = fitLayout(sides, 600, 400, 50);
      for (const p of [L.A, L.B, L.C]) {
        expect(p.x).toBeGreaterThanOrEqual(50 - 1e-9);
        expect(p.x).toBeLessThanOrEqual(550 + 1e-9);
        expect(p.y).toBeGreaterThanOrEqual(50 - 1e-9);
        expect(p.y).toBeLessThanOrEqual(350 + 1e-9);
      }
      expect(dist(L.B, L.C) / dist(L.A, L.B)).toBeCloseTo(sides.a / sides.c);
      expect(dist(L.A, L.C) / dist(L.A, L.B)).toBeCloseTo(sides.b / sides.c);
    }
  });

  it("keeps the circumcircle inside the box when requested", () => {
    const L = fitLayout({ a: 10, b: 5.5, c: 5 }, 600, 400, 50, true);
    const { center, radius } = L.circumcircle;
    expect(center.x - radius).toBeGreaterThanOrEqual(50 - 1e-6);
    expect(center.y + radius).toBeLessThanOrEqual(350 + 1e-6);
  });

  it("computes the 3-4-5 circles", () => {
    const { A, B, C } = rawVertices({ a: 3, b: 4, c: 5 });
    expect(circumcircle(A, B, C).radius).toBeCloseTo(2.5);
    expect(incircle(A, B, C).radius).toBeCloseTo(1);
  });

  it("builds a closed angle arc path", () => {
    const arc = angleArc({ x: 0, y: 0 }, { x: 100, y: 0 }, { x: 0, y: 100 });
    expect(arc.path).toMatch(/^M 0 0 L .* A .* Z$/);
    expect(arc.label.x).toBeGreaterThan(0);
    expect(arc.label.y).toBeGreaterThan(0);
  });

  it("checks the triangle inequality", () => {
    expect(formsTriangle({ a: 3, b: 4, c: 5 })).toBe(true);
    expect(formsTriangle({ a: 1, b: 2, c: 3 })).toBe(false);
  });

  it("detects SSA", () => {
    expect(isSSA({ a: 3, b: 4, A: 30 })).toBe(true);
    expect(isSSA({ b: 3, c: 4, A: 90 })).toBe(false);
    expect(isSSA({ a: 3, b: 4 })).toBe(false);
  });
});

describe("construction eligibility", () => {
  it("is a placeholder without a response or when stale", () => {
    expect(visualState(null, false)).toEqual({ kind: "placeholder", reason: "empty" });
    expect(visualState(response({ facts: { a: 3, b: 4, c: 5 } }), true)).toEqual({ kind: "placeholder", reason: "stale" });
  });
  it("constructs from three derived sides, even when UNRESOLVED", () => {
    expect(visualState(response({ status: "UNRESOLVED", facts: { a: 3, b: 4, c: 5 } }), false))
      .toEqual({ kind: "constructed", sides: { a: 3, b: 4, c: 5 }, normalized: false });
  });
  it("never draws INVALID or INCONSISTENT results", () => {
    expect(visualState(response({ status: "INVALID", facts: { a: 1, b: 2, c: 3 } }), false).kind).toBe("invalid");
    expect(visualState(response({ status: "INCONSISTENT", facts: { a: 3, b: 4, c: 5, S: 7 } }), false).kind).toBe("inconsistent");
  });
  it("normalizes AAA and flags SSA as ambiguous", () => {
    expect(visualState(response({ status: "UNRESOLVED", facts: { A: 50, B: 60, C: 70 } }), false)).toMatchObject({ kind: "constructed", normalized: true });
    expect(visualState(response({ status: "UNRESOLVED", facts: { a: 3, b: 4, A: 30, R: 3 } }), false).kind).toBe("ambiguous");
    expect(visualState(response({ status: "UNRESOLVED", facts: { a: 3 } }), false)).toEqual({ kind: "placeholder", reason: "insufficient" });
  });
});

describe("api client", () => {
  afterEach(() => vi.unstubAllGlobals());
  const stubFetch = (impl: () => Promise<unknown>) => {
    const fn = vi.fn(impl);
    vi.stubGlobal("fetch", fn);
    return fn;
  };

  it("posts the request and returns the response", async () => {
    const body = response({ facts: { a: 3 } });
    const fetch = stubFetch(async () => new Response(JSON.stringify(body), { status: 200 }));
    await expect(solve({ facts: { a: 3 }, goals: ["S"] }, undefined, "http://x")).resolves.toEqual(body);
    expect(fetch).toHaveBeenCalledWith("http://x/api/v1/solve", expect.objectContaining({
      method: "POST", body: JSON.stringify({ facts: { a: 3 }, goals: ["S"] }),
    }));
  });
  it("reports network failures", async () => {
    stubFetch(async () => { throw new TypeError("Failed to fetch"); });
    await expect(solve({ facts: {}, goals: ["S"] })).rejects.toMatchObject({ kind: "network" });
  });
  it("reports HTTP errors with details", async () => {
    stubFetch(async () => new Response(JSON.stringify({ detail: [{ msg: "bad goal" }] }), { status: 422 }));
    await expect(solve({ facts: {}, goals: ["S"] })).rejects.toThrow(/HTTP 422.*bad goal/);
  });
  it("rejects unexpected response shapes", async () => {
    stubFetch(async () => new Response(JSON.stringify({ status: "WEIRD" }), { status: 200 }));
    const error = await solve({ facts: {}, goals: ["S"] }).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.kind).toBe("format");
  });
  it("rejects non-JSON bodies", async () => {
    stubFetch(async () => new Response("<html>", { status: 500 }));
    await expect(solve({ facts: {}, goals: ["S"] })).rejects.toMatchObject({ kind: "format", status: 500 });
  });
});
