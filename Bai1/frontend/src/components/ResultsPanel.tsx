import { AlertTriangle, CheckCircle2, CircleHelp, History, PenLine, RefreshCw, Sparkles, XCircle } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sym } from "@/components/Sym";
import type { ApiError, SolveResponse } from "@/lib/api";
import { formatValue, prettyFormula } from "@/lib/format";
import { explainMessage, STATUS_UI } from "@/lib/status";
import { relevantSteps } from "@/lib/trace";
import { cn } from "@/lib/utils";
import { GROUP_NAMES, VARIABLE_NAMES, VARIABLES, unitOf, type Variable } from "@/lib/variables";

export interface SolveResult { response: SolveResponse; given: Set<Variable>; goals: Variable[]; mode: "selected" | "all" }

interface Props {
  result: SolveResult | null;
  stale: boolean;
  error: ApiError | null;
  onRetry: () => void;
  selected: Variable | null;
  onSelect: (v: Variable | null) => void;
  selectedStep: number | null;
  onSelectStep: (step: number | null) => void;
  stepsOpen: boolean;
  onStepsOpen: (open: boolean) => void;
  stepView: "relevant" | "all";
  onStepView: (view: "relevant" | "all") => void;
}

const TONE_ICON = { success: CheckCircle2, warning: AlertTriangle, danger: XCircle };
const TONE_BOX = {
  success: "border-success/25 bg-success/5",
  warning: "border-warning/30 bg-warning/5",
  danger: "border-danger/25 bg-danger/5",
};

type Origin = "given" | "inferred" | "unresolved";
function originOf(v: Variable, r: SolveResult): Origin {
  if (r.given.has(v)) return "given";
  return r.response.facts[v] !== undefined ? "inferred" : "unresolved";
}

function OriginBadge({ origin }: { origin: Origin }) {
  if (origin === "given") return <Badge tone="neutral"><PenLine aria-hidden />Given</Badge>;
  if (origin === "inferred") return <Badge tone="info"><Sparkles aria-hidden />Inferred</Badge>;
  return <Badge tone="warning"><CircleHelp aria-hidden />Unresolved</Badge>;
}

function valueOf(v: Variable, r: SolveResult) {
  const value = r.response.facts[v];
  return value === undefined ? "—" : `${formatValue(value)}${unitOf(v)}`;
}

export function ResultsPanel(p: Props) {
  const r = p.result;
  return (
    <Card aria-labelledby="results-title">
      <CardHeader>
        <CardTitle id="results-title">Results</CardTitle>
        {r && <Badge tone={STATUS_UI[r.response.status].tone} data-testid="status-badge">{r.response.status}</Badge>}
      </CardHeader>
      <CardContent className="space-y-4">
        {p.error && (
          <div role="alert" className="flex flex-col gap-3 rounded-lg border border-danger/25 bg-danger/5 p-3 text-sm sm:flex-row sm:items-center sm:justify-between">
            <p className="flex items-start gap-2 text-danger"><XCircle className="mt-0.5 size-4 shrink-0" aria-hidden />{p.error.message}</p>
            <Button variant="outline" size="sm" onClick={p.onRetry}><RefreshCw aria-hidden />Retry</Button>
          </div>
        )}
        {!r && !p.error && <p className="text-sm text-muted-foreground">Enter known parameters, choose what to find, then press Solve.</p>}
        {r && <Body {...p} r={r} />}
      </CardContent>
    </Card>
  );
}

function Body(p: Props & { r: SolveResult }) {
  const { r } = p;
  const { status, message, trace, facts } = r.response;
  const ui = STATUS_UI[status];
  const Icon = TONE_ICON[ui.tone];
  const showValues = status === "SOLVED" || status === "UNRESOLVED";
  const extra = VARIABLES.filter((v) => facts[v] !== undefined && !r.goals.includes(v) && !r.given.has(v));
  const known = VARIABLES.filter((v) => facts[v] !== undefined).length;
  const summary = r.mode === "all" && status !== "INVALID" && status !== "INCONSISTENT"
    ? `Calculated everything the knowledge base can derive: ${known} of 13 values known.${status === "UNRESOLVED" ? " The rest cannot be derived from these facts." : ""}`
    : explainMessage(status, message, r.response.reason_code);
  const sel = p.selected;
  const relevant = sel && p.stepView === "relevant" ? relevantSteps(trace, sel) : trace;

  return (
    <div className={cn("space-y-4", p.stale && "opacity-60")} data-stale={p.stale}>
      <div role="status" aria-live="polite" className={cn("rounded-lg border p-3 text-sm", TONE_BOX[ui.tone])}>
        <p className="flex items-center gap-2 font-medium"><Icon className="size-4 shrink-0" aria-hidden />{ui.label}</p>
        <p className="mt-1 text-foreground/80">{summary}</p>
        {status !== "SOLVED" && <p className="mt-1 break-words font-mono text-xs text-muted-foreground">Solver: {message}</p>}
      </div>

      {p.stale && (
        <p role="status" className="flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/5 p-3 text-sm text-warning" data-testid="stale-banner">
          <History className="size-4 shrink-0" aria-hidden />Inputs changed since this result. Solve again to update it.
        </p>
      )}

      {showValues && (
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3" aria-label="Requested values">
          {r.goals.map((v) => {
            const origin = originOf(v, r);
            const on = p.selected === v;
            return (
              <li key={v}>
                <button
                  type="button"
                  aria-pressed={on}
                  data-testid={`result-${v}`}
                  onClick={() => p.onSelect(on ? null : v)}
                  className={cn(
                    "flex w-full items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring motion-safe:transition-colors",
                    on ? "border-primary bg-primary/5" : "border-border hover:border-primary/40",
                  )}
                >
                  <span className="min-w-0">
                    <span className="block text-xs text-muted-foreground">{VARIABLE_NAMES[v]}</span>
                    <span className={cn("block text-lg tabular-nums", origin === "inferred" ? "text-primary" : origin === "unresolved" && "text-muted-foreground")}>
                      <Sym v={v} /> = <span data-testid={`value-${v}`}>{valueOf(v, r)}</span>
                    </span>
                  </span>
                  <OriginBadge origin={origin} />
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {showValues && extra.length > 0 && (
        <div className="text-sm">
          <p className="mb-1.5 text-xs text-muted-foreground">Intermediate values also derived</p>
          <div className="flex flex-wrap gap-1.5">
            {extra.map((v) => (
              <button key={v} type="button" aria-pressed={p.selected === v} onClick={() => p.onSelect(p.selected === v ? null : v)}
                className={cn("rounded-full border px-2.5 py-1 text-xs tabular-nums text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  p.selected === v ? "border-primary bg-primary/5" : "border-border hover:border-primary/40")}>
                <Sym v={v} /> = {valueOf(v, r)}
              </button>
            ))}
          </div>
        </div>
      )}

      <Accordion type="single" collapsible value={p.stepsOpen ? "steps" : ""} onValueChange={(v) => p.onStepsOpen(v === "steps")}>
        <AccordionItem value="steps" className="border-t">
          <AccordionTrigger>Solution steps <span className="ml-auto mr-1 text-xs font-normal text-muted-foreground">{trace.length} {trace.length === 1 ? "step" : "steps"}</span></AccordionTrigger>
          <AccordionContent>
            {trace.length === 0 ? (
              <p className="text-muted-foreground">No inference rules were applied{status === "SOLVED" ? ": every requested value was given." : "."}</p>
            ) : (
              <>
                {sel && facts[sel] !== undefined && (
                  <div className="mb-3 flex flex-wrap items-center gap-2 text-xs" role="group" aria-label="Which steps to show">
                    {(["relevant", "all"] as const).map((view) => (
                      <Button key={view} size="sm" variant={p.stepView === view ? "secondary" : "ghost"} className="h-7 px-2 text-xs" aria-pressed={p.stepView === view} onClick={() => p.onStepView(view)}>
                        {view === "relevant" ? <>Steps for&nbsp;<Sym v={sel} /></> : "Full trace"}
                      </Button>
                    ))}
                    {relevant.length === 0 && <span className="text-muted-foreground"><Sym v={sel} /> was given, so no step derives it.</span>}
                  </div>
                )}
                <ol className="space-y-2" aria-label="Inference trace">
                  {relevant.map((s) => {
                    const on = p.selectedStep === s.step;
                    return (
                      <li key={s.step}>
                        <button type="button" aria-pressed={on} data-testid={`step-${s.step}`} onClick={() => p.onSelectStep(on ? null : s.step)}
                          className={cn("w-full rounded-lg border p-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring motion-safe:transition-colors",
                            on ? "border-primary bg-primary/5" : "border-border hover:border-primary/40")}>
                          <span className="flex flex-wrap items-center gap-2">
                            <span className="font-medium">Step {s.step}</span>
                            <Badge tone="info" className="font-mono">{s.rule_id}</Badge>
                            <span className="text-xs text-muted-foreground">{s.group} · {GROUP_NAMES[s.group] ?? s.group}</span>
                          </span>
                          <span className="mt-2 block break-words font-mono text-[13px]">{prettyFormula(s.formula)}</span>
                          <span className="mt-1.5 block text-xs text-muted-foreground">
                            Using {(Object.entries(s.inputs) as [Variable, number][]).map(([v, x], i) => (
                              <span key={v}>{i > 0 && ", "}<Sym v={v} /> = {formatValue(x)}{unitOf(v)}</span>
                            ))}
                          </span>
                          <span className="mt-1 block text-sm text-primary">→ <Sym v={s.output} /> = {formatValue(s.value)}{unitOf(s.output)}</span>
                        </button>
                      </li>
                    );
                  })}
                </ol>
              </>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
