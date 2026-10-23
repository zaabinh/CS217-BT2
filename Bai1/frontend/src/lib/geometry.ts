import type { Facts, SolveResponse } from "./api";

/**
 * Geometry here only positions SVG elements. Every mathematical value shown
 * to the user comes from the backend response.
 */
export interface Point { x: number; y: number }
export interface Sides { a: number; b: number; c: number }

export type VisualState =
  | { kind: "placeholder"; reason: "empty" | "insufficient" | "stale" }
  | { kind: "constructed"; sides: Sides; normalized: boolean }
  | { kind: "ambiguous" }
  | { kind: "invalid"; message: string }
  | { kind: "inconsistent"; message: string };

const OPPOSITE: Record<"a" | "b" | "c", "A" | "B" | "C"> = { a: "A", b: "B", c: "C" };
const deg = (x: number) => (x * Math.PI) / 180;

/** Solver status and drawing state are separate: UNRESOLVED may still determine a triangle. */
export function visualState(response: SolveResponse | null, stale: boolean): VisualState {
  if (!response) return { kind: "placeholder", reason: "empty" };
  if (stale) return { kind: "placeholder", reason: "stale" };
  if (response.status === "INVALID") return { kind: "invalid", message: response.message };
  if (response.status === "INCONSISTENT") return { kind: "inconsistent", message: response.message };
  const f = response.facts;
  if (f.a !== undefined && f.b !== undefined && f.c !== undefined) {
    const sides = { a: f.a, b: f.b, c: f.c };
    return formsTriangle(sides) ? { kind: "constructed", sides, normalized: false } : { kind: "placeholder", reason: "insufficient" };
  }
  // AAA fixes the shape but not the scale; the backend derives every side as soon as one is known.
  if (f.A !== undefined && f.B !== undefined && f.C !== undefined) {
    return { kind: "constructed", sides: { a: Math.sin(deg(f.A)), b: Math.sin(deg(f.B)), c: Math.sin(deg(f.C)) }, normalized: true };
  }
  if (isSSA(f)) return { kind: "ambiguous" };
  return { kind: "placeholder", reason: "insufficient" };
}

/** Two sides and an angle opposite one of them, with the included angle unknown. */
export function isSSA(f: Facts): boolean {
  const known = (["a", "b", "c"] as const).filter((s) => f[s] !== undefined);
  if (known.length !== 2) return false;
  const missing = (["a", "b", "c"] as const).find((s) => f[s] === undefined)!;
  return f[OPPOSITE[missing]] === undefined && known.some((s) => f[OPPOSITE[s]] !== undefined);
}

export function formsTriangle({ a, b, c }: Sides): boolean {
  const [x, y, z] = [a, b, c].sort((p, q) => p - q);
  return x > 0 && x > z - y;
}

/** Vertex positions with B at the origin, C on the x axis and A above it (y grows upward). */
export function rawVertices({ a, b, c }: Sides): Record<"A" | "B" | "C", Point> {
  const x = (c * c + a * a - b * b) / (2 * a);
  const y = Math.sqrt(Math.max(0, c * c - x * x));
  return { A: { x, y }, B: { x: 0, y: 0 }, C: { x: a, y: 0 } };
}

export const dist = (p: Point, q: Point) => Math.hypot(p.x - q.x, p.y - q.y);

export function circumcircle(A: Point, B: Point, C: Point): { center: Point; radius: number } {
  const d = 2 * (A.x * (B.y - C.y) + B.x * (C.y - A.y) + C.x * (A.y - B.y));
  const sq = (p: Point) => p.x * p.x + p.y * p.y;
  const center = {
    x: (sq(A) * (B.y - C.y) + sq(B) * (C.y - A.y) + sq(C) * (A.y - B.y)) / d,
    y: (sq(A) * (C.x - B.x) + sq(B) * (A.x - C.x) + sq(C) * (B.x - A.x)) / d,
  };
  return { center, radius: dist(center, A) };
}

export function incircle(A: Point, B: Point, C: Point): { center: Point; radius: number } {
  const a = dist(B, C), b = dist(A, C), c = dist(A, B);
  const per = a + b + c;
  const center = { x: (a * A.x + b * B.x + c * C.x) / per, y: (a * A.y + b * B.y + c * C.y) / per };
  const area = Math.abs((B.x - A.x) * (C.y - A.y) - (C.x - A.x) * (B.y - A.y)) / 2;
  return { center, radius: area / (per / 2) };
}

/** Foot of the perpendicular from P to the line through Q1, Q2 (may lie outside the segment). */
export function foot(P: Point, Q1: Point, Q2: Point): Point {
  const dx = Q2.x - Q1.x, dy = Q2.y - Q1.y;
  const t = ((P.x - Q1.x) * dx + (P.y - Q1.y) * dy) / (dx * dx + dy * dy);
  return { x: Q1.x + t * dx, y: Q1.y + t * dy };
}

export interface Layout {
  A: Point; B: Point; C: Point;
  incircle: { center: Point; radius: number };
  circumcircle: { center: Point; radius: number };
}

/**
 * Scale uniformly into a width×height box with a margin, centering the result.
 * SVG y grows downward, so y is flipped. The circumcircle joins the bounding box only on request,
 * because it can be much larger than the triangle itself.
 */
export function fitLayout(sides: Sides, width: number, height: number, margin: number, withCircumcircle = false): Layout {
  const v = rawVertices(sides);
  const circ = circumcircle(v.A, v.B, v.C);
  const xs = [v.A.x, v.B.x, v.C.x], ys = [v.A.y, v.B.y, v.C.y];
  if (withCircumcircle) {
    xs.push(circ.center.x - circ.radius, circ.center.x + circ.radius);
    ys.push(circ.center.y - circ.radius, circ.center.y + circ.radius);
  }
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const bw = maxX - minX, bh = Math.max(maxY - minY, 1e-12);
  const scale = Math.min((width - 2 * margin) / bw, (height - 2 * margin) / bh);
  const ox = (width - bw * scale) / 2, oy = (height - bh * scale) / 2;
  const map = (p: Point): Point => ({ x: ox + (p.x - minX) * scale, y: height - (oy + (p.y - minY) * scale) });
  const A = map(v.A), B = map(v.B), C = map(v.C);
  return { A, B, C, incircle: incircle(A, B, C), circumcircle: circumcircle(A, B, C) };
}

const unit = (p: Point, q: Point): Point => {
  const d = dist(p, q) || 1;
  return { x: (q.x - p.x) / d, y: (q.y - p.y) / d };
};

/** Arc path for the interior angle at `at`, plus a label position along the bisector. */
export function angleArc(at: Point, p: Point, q: Point, maxRadius = 30): { path: string; label: Point } {
  const radius = Math.max(8, Math.min(maxRadius, 0.3 * Math.min(dist(at, p), dist(at, q))));
  const u = unit(at, p), w = unit(at, q);
  const start = { x: at.x + u.x * radius, y: at.y + u.y * radius };
  const end = { x: at.x + w.x * radius, y: at.y + w.y * radius };
  const sweep = u.x * w.y - u.y * w.x > 0 ? 1 : 0;
  const bis = unit({ x: 0, y: 0 }, { x: u.x + w.x, y: u.y + w.y });
  const r = radius + 22;
  return {
    path: `M ${at.x} ${at.y} L ${start.x} ${start.y} A ${radius} ${radius} 0 0 ${sweep} ${end.x} ${end.y} Z`,
    label: { x: at.x + bis.x * r, y: at.y + bis.y * r },
  };
}

/** Point offset from `p` away from `from`, used to push labels outside the triangle. */
export function pushAway(p: Point, from: Point, distance: number): Point {
  const u = unit(from, p);
  return { x: p.x + u.x * distance, y: p.y + u.y * distance };
}

export const centroid = (A: Point, B: Point, C: Point): Point => ({ x: (A.x + B.x + C.x) / 3, y: (A.y + B.y + C.y) / 3 });
