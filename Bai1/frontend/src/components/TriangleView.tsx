import { useEffect, useRef, useState } from "react";
import { Maximize2, Minimize2, RotateCcw, Tag } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Facts } from "@/lib/api";
import { formatValue } from "@/lib/format";
import { angleArc, centroid, foot, fitLayout, pushAway, type Point, type VisualState } from "@/lib/geometry";
import { cn } from "@/lib/utils";
import { VARIABLE_NAMES, unitOf, type Variable } from "@/lib/variables";

export interface Highlight { primary: Set<Variable>; secondary: Set<Variable> }

interface Props {
  state: VisualState;
  facts: Facts;
  given: Set<Variable>;
  highlight: Highlight;
  onSelect: (v: Variable) => void;
  onResetView: () => void;
}

const margin = (W: number) => (W < 500 ? 40 : 56);

const MESSAGES: Record<Exclude<VisualState["kind"], "constructed">, string> = {
  placeholder: "Enter sufficient parameters to construct a triangle.",
  ambiguous: "More than one triangle fits these facts (two sides and a non-included angle). The solver does not pick one, so none is drawn.",
  invalid: "These values cannot form a triangle, so nothing is drawn.",
  inconsistent: "The facts conflict with each other, so no triangle is drawn.",
};

export function describeVar(v: Variable, facts: Facts, given: Set<Variable>): string {
  const value = facts[v];
  if (value === undefined) return `${v}: ${VARIABLE_NAMES[v]}, unknown`;
  return `${v} = ${formatValue(value)}${unitOf(v)}: ${VARIABLE_NAMES[v]}, ${given.has(v) ? "given" : "inferred"}`;
}

export function TriangleView({ state, facts, given, highlight, onSelect, onResetView }: Props) {
  const [hovered, setHovered] = useState<Variable | null>(null);
  const [labels, setLabels] = useState(true);
  const [expanded, setExpanded] = useState(false);
  // The viewBox follows the rendered width so label font sizes stay in real pixels on every screen.
  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(600);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => entry.contentRect.width > 0 && setW(Math.round(entry.contentRect.width)));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const H = Math.round(Math.max(260, W * (expanded ? 0.8 : W < 500 ? 0.85 : 0.63)));

  const focusVar = hovered ?? (highlight.primary.size === 1 ? [...highlight.primary][0] : null);
  const placeholderMessage = state.kind === "placeholder" && state.reason === "stale"
    ? "Inputs changed. Solve again to update the triangle."
    : state.kind !== "constructed" ? MESSAGES[state.kind] : "";

  return (
    <Card aria-labelledby="viz-title">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle id="viz-title">Triangle</CardTitle>
          {state.kind === "constructed" && (state.normalized
            ? <Badge tone="warning">Scale-normalized: shape only</Badge>
            : <Badge tone="info">To scale</Badge>)}
          {state.kind === "ambiguous" && <Badge tone="warning">Ambiguous</Badge>}
          {state.kind === "invalid" && <Badge tone="danger">Invalid</Badge>}
          {state.kind === "inconsistent" && <Badge tone="danger">Inconsistent</Badge>}
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" className="size-9" onClick={() => { setHovered(null); onResetView(); }} aria-label="Reset view" title="Reset view"><RotateCcw aria-hidden /></Button>
          <Button variant="ghost" size="icon" className="size-9" aria-pressed={labels} onClick={() => setLabels(!labels)} aria-label="Show labels" title="Toggle labels"><Tag aria-hidden /></Button>
          <Button variant="ghost" size="icon" className="hidden size-9 sm:inline-flex" aria-pressed={expanded} onClick={() => setExpanded(!expanded)} aria-label="Expand visualization" title="Expand">
            {expanded ? <Minimize2 aria-hidden /> : <Maximize2 aria-hidden />}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div ref={box} className="overflow-hidden rounded-lg border border-border bg-[radial-gradient(circle,#e2e8f0_1px,transparent_1px)] [background-size:20px_20px]">
          {state.kind === "constructed"
            ? <Constructed {...{ state, facts, given, highlight, onSelect, labels, W, H }} onHover={setHovered} />
            : <Placeholder kind={state.kind} message={placeholderMessage} W={W} H={H} />}
        </div>
        <p className="mt-2 min-h-5 text-xs text-muted-foreground" aria-live="polite">
          {state.kind === "constructed" && focusVar
            ? describeVar(focusVar, facts, given)
            : state.kind === "constructed"
              ? "Hover, focus or click a side or angle to inspect it. Inferred values are blue and underlined."
              : ""}
        </p>
      </CardContent>
    </Card>
  );
}

function Placeholder({ kind, message, W, H }: { kind: VisualState["kind"]; message: string; W: number; H: number }) {
  const tone = kind === "invalid" || kind === "inconsistent" ? "stroke-danger/60" : kind === "ambiguous" ? "stroke-warning/70" : "stroke-muted-foreground/40";
  const cy = H / 2 - 20, k = Math.min(W / 600, H / 380);
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" role="img" aria-label="Illustrative triangle, not to scale">
        <polygon points={`${W / 2},${cy - 110 * k} ${W / 2 - 150 * k},${cy + 90 * k} ${W / 2 + 170 * k},${cy + 90 * k}`} className={cn("fill-none", tone)} strokeWidth={2} strokeDasharray="8 6" />
      </svg>
      <p role="status" data-testid="viz-message" className="absolute inset-x-4 bottom-5 text-center text-sm text-muted-foreground">{message}</p>
    </div>
  );
}

interface ConstructedProps {
  state: Extract<VisualState, { kind: "constructed" }>;
  facts: Facts; given: Set<Variable>; highlight: Highlight;
  onSelect: (v: Variable) => void; onHover: (v: Variable | null) => void;
  labels: boolean; W: number; H: number;
}

function Constructed({ state, facts, given, highlight, onSelect, onHover, labels, W, H }: ConstructedProps) {
  const on = (v: Variable) => highlight.primary.has(v) || highlight.secondary.has(v);
  const L = fitLayout(state.sides, W, H, margin(W), on("R"));
  const { A, B, C } = L;
  const G = centroid(A, B, C);
  const sideActive = (v: Variable) => on(v) || on("p");

  const valueText = (v: Variable, prefix = true) => {
    const value = facts[v];
    if (value === undefined || (state.normalized && (v === "a" || v === "b" || v === "c"))) return prefix ? v : "";
    return `${prefix ? `${v} = ` : ""}${formatValue(value)}${unitOf(v)}`;
  };
  const inferred = (v: Variable) => facts[v] !== undefined && !given.has(v);
  const tone = (v: Variable) => highlight.primary.has(v) ? "primary" : highlight.secondary.has(v) ? "secondary" : null;

  const interactive = (v: Variable) => ({
    tabIndex: 0,
    role: "button",
    "aria-label": describeVar(v, facts, given),
    onClick: () => onSelect(v),
    onKeyDown: (e: React.KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(v); } },
    onMouseEnter: () => onHover(v), onMouseLeave: () => onHover(null),
    onFocus: () => onHover(v), onBlur: () => onHover(null),
    className: "cursor-pointer outline-none [&:focus-visible>.hit]:stroke-primary/25",
  });

  const label = (p: Point, text: string, v: Variable, extra = "") => (
    <text x={p.x} y={p.y} textAnchor="middle" dominantBaseline="central"
      className={cn("pointer-events-none select-none text-[15px] stroke-card [paint-order:stroke] [stroke-linejoin:round] [stroke-width:5px]", inferred(v) ? "fill-primary underline decoration-dotted" : "fill-foreground", tone(v) && "font-semibold", extra)}>
      {text}
    </text>
  );

  const side = (v: "a" | "b" | "c", p: Point, q: Point) => {
    const mid = { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 };
    return (
      <g key={v} {...interactive(v)} data-testid={`side-${v}`} data-highlight={tone(v) ?? (sideActive(v) ? "secondary" : "none")}>
        <line className="hit" x1={p.x} y1={p.y} x2={q.x} y2={q.y} stroke="transparent" strokeWidth={18} strokeLinecap="round" />
        <line x1={p.x} y1={p.y} x2={q.x} y2={q.y} strokeLinecap="round"
          className={cn(sideActive(v) ? "stroke-primary" : "stroke-foreground")} strokeWidth={tone(v) === "primary" ? 4.5 : sideActive(v) ? 3.5 : 2.25} />
        {labels && label(pushAway(mid, G, 18), valueText(v), v)}
      </g>
    );
  };

  const angle = (v: "A" | "B" | "C", at: Point, p: Point, q: Point) => {
    const arc = angleArc(at, p, q);
    const known = facts[v] !== undefined;
    return (
      <g key={v} {...interactive(v)} data-testid={`angle-${v}`} data-highlight={tone(v) ?? "none"}>
        <path d={arc.path} className={cn(on(v) ? "fill-primary/25 stroke-primary" : known ? "fill-primary/5 stroke-muted-foreground/60" : "fill-transparent stroke-transparent")} strokeWidth={1.5} />
        <circle className="hit" cx={at.x} cy={at.y} r={14} fill="transparent" stroke="transparent" strokeWidth={6} />
        <circle cx={at.x} cy={at.y} r={on(v) ? 5 : 3.5} className={on(v) ? "fill-primary" : "fill-foreground"} />
        {label(pushAway(at, G, 20), v, v, "font-semibold fill-foreground no-underline")}
        {labels && known && label(arc.label, valueText(v, false), v, "text-[12px]")}
      </g>
    );
  };

  const altitude = (v: "ha" | "hb" | "hc", from: Point, p: Point, q: Point) => {
    const f = foot(from, p, q);
    const t = ((f.x - p.x) * (q.x - p.x) + (f.y - p.y) * (q.y - p.y)) / ((q.x - p.x) ** 2 + (q.y - p.y) ** 2);
    const near = t < 0 ? p : q;
    return (
      <g key={v} data-testid={`altitude-${v}`} className="pointer-events-none">
        {(t < 0 || t > 1) && <line x1={near.x} y1={near.y} x2={f.x} y2={f.y} className="stroke-muted-foreground" strokeWidth={1.5} strokeDasharray="4 4" />}
        <line x1={from.x} y1={from.y} x2={f.x} y2={f.y} className="stroke-primary" strokeWidth={2.5} strokeDasharray="6 4" />
        <circle cx={f.x} cy={f.y} r={3} className="fill-primary" />
        {labels && label(pushAway({ x: (from.x + f.x) / 2, y: (from.y + f.y) / 2 }, near === p ? q : p, -22), valueText(v), v, "text-[13px]")}
      </g>
    );
  };

  const summary = `Triangle with vertices A, B, C${state.normalized ? ", drawn scale-normalized from its angles" : ""}. `
    + (["a", "b", "c", "A", "B", "C"] as Variable[]).map((v) => describeVar(v, facts, given)).join("; ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" role="group" aria-label="Triangle visualization" data-testid="triangle-svg">
      <desc>{summary}</desc>
      <polygon points={`${A.x},${A.y} ${B.x},${B.y} ${C.x},${C.y}`} data-testid="triangle-area"
        className={cn(on("S") ? "fill-primary/15" : "fill-card/70", "motion-safe:transition-colors")} />
      {on("R") && <circle data-testid="circumcircle" cx={L.circumcircle.center.x} cy={L.circumcircle.center.y} r={L.circumcircle.radius} className="fill-none stroke-primary" strokeWidth={1.75} strokeDasharray="6 4" />}
      {on("r") && <circle data-testid="incircle" cx={L.incircle.center.x} cy={L.incircle.center.y} r={L.incircle.radius} className="fill-primary/5 stroke-primary" strokeWidth={1.75} />}
      {on("ha") && altitude("ha", A, B, C)}
      {on("hb") && altitude("hb", B, A, C)}
      {on("hc") && altitude("hc", C, A, B)}
      {side("a", B, C)}
      {side("b", A, C)}
      {side("c", A, B)}
      {angle("A", A, B, C)}
      {angle("B", B, A, C)}
      {angle("C", C, A, B)}
    </svg>
  );
}
