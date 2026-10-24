import { useMemo, useRef, useState } from "react";
import { CircleHelp, RotateCcw, Triangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { TooltipProvider } from "@/components/ui/tooltip";
import { InputPanel } from "@/components/InputPanel";
import { ResultsPanel, type SolveResult } from "@/components/ResultsPanel";
import { TriangleView, type Highlight } from "@/components/TriangleView";
import { ApiError, solve as solveApi } from "@/lib/api";
import { EXAMPLES } from "@/lib/examples";
import { visualState } from "@/lib/geometry";
import { buildFacts, parseAll, type RawInputs } from "@/lib/input";
import { VARIABLES, type Variable } from "@/lib/variables";

type Mode = "selected" | "all";

export default function App({ solve = solveApi }: { solve?: typeof solveApi }) {
  const [raw, setRaw] = useState<RawInputs>({});
  const [targets, setTargets] = useState<Set<Variable>>(new Set());
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SolveResult | null>(null);
  const [stale, setStale] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [selected, setSelected] = useState<Variable | null>(null);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [stepsOpen, setStepsOpen] = useState(false);
  const [stepView, setStepView] = useState<"relevant" | "all">("relevant");

  // Only the newest request may update state; older ones are aborted and ignored.
  const requestId = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  const lastMode = useRef<Mode>("selected");

  const fields = useMemo(() => parseAll(raw), [raw]);
  const hasInvalid = Object.values(fields).some((f) => f.kind === "invalid");

  const clearSelection = () => { setSelected(null); setSelectedStep(null); };

  const invalidate = () => {
    requestId.current++;
    inFlight.current?.abort();
    setLoading(false);
    setError(null);
    if (result) setStale(true);
    clearSelection();
  };

  const onChange = (v: Variable, value: string) => {
    invalidate();
    setRaw((prev) => ({ ...prev, [v]: value }));
  };

  async function runSolve(mode: Mode) {
    const facts = buildFacts(raw);
    if (!facts) return;
    const goals = mode === "all" ? [...VARIABLES] : VARIABLES.filter((v) => targets.has(v));
    if (goals.length === 0) return;
    lastMode.current = mode;
    const id = ++requestId.current;
    inFlight.current?.abort();
    const controller = new AbortController();
    inFlight.current = controller;
    setLoading(true);
    try {
      const response = await solve({ facts, goals }, controller.signal);
      if (id !== requestId.current) return;
      setResult({ response, given: new Set(Object.keys(facts) as Variable[]), goals, mode });
      setStale(false);
      setError(null);
      clearSelection();
    } catch (e) {
      if (id !== requestId.current || (e as Error).name === "AbortError") return;
      setError(e instanceof ApiError ? e : new ApiError(`Unexpected error: ${(e as Error).message}`, "format"));
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }

  const reset = () => {
    requestId.current++;
    inFlight.current?.abort();
    setRaw({}); setTargets(new Set()); setResult(null); setStale(false); setError(null);
    setLoading(false); setAdvancedOpen(false); setStepsOpen(false); clearSelection();
  };

  const loadExample = (id: string) => {
    const example = EXAMPLES.find((e) => e.id === id);
    if (!example) return;
    reset();
    setRaw(example.inputs);
    setTargets(new Set(example.targets));
  };

  const selectResult = (v: Variable | null) => {
    setSelected(v);
    setSelectedStep(null);
    setStepView("relevant");
    if (v) setStepsOpen(true);
  };

  const highlight: Highlight = useMemo(() => {
    const step = selectedStep !== null ? result?.response.trace.find((s) => s.step === selectedStep) : undefined;
    if (step) return { primary: new Set([step.output]), secondary: new Set(Object.keys(step.inputs) as Variable[]) };
    return { primary: new Set(selected ? [selected] : []), secondary: new Set() };
  }, [selected, selectedStep, result]);

  return (
    <TooltipProvider delayDuration={300}>
      <div className="min-h-screen">
        <header className="border-b border-border bg-card">
          <div className="mx-auto flex h-14 max-w-[1400px] items-center justify-between gap-3 px-4">
            <div className="flex min-w-0 items-center gap-2.5">
              <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary"><Triangle className="size-4" aria-hidden /></span>
              <h1 className="truncate font-semibold tracking-tight">Triangle Solver</h1>
              <span className="hidden text-sm text-muted-foreground sm:inline">Computational Network</span>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="sm" onClick={reset}><RotateCcw aria-hidden />Reset</Button>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="sm"><CircleHelp aria-hidden />Help</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogTitle className="text-base font-semibold">About Triangle Solver</DialogTitle>
                  <DialogDescription className="mt-1 text-sm text-muted-foreground">
                    A knowledge-based system: 13 variables, 10 relation groups and 46 directed rules, applied by forward chaining.
                  </DialogDescription>
                  <ol className="mt-4 list-decimal space-y-1.5 pl-5 text-sm">
                    <li>Enter the values you know. Lengths share one unit; angles are in degrees.</li>
                    <li>Pick what to find, or use <em>Calculate all possible</em>.</li>
                    <li>Press <em>Solve selected</em>. Nothing is computed until you do.</li>
                    <li>Click a result to highlight it on the triangle and see the rules that derived it.</li>
                  </ol>
                  <p className="mt-4 text-xs text-muted-foreground">
                    All values come from the Python backend. The drawing is built from the sides it derives. Unresolved means
                    the rule set cannot derive the value, not that no triangle exists.
                  </p>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </header>

        <main className="mx-auto grid max-w-[1400px] gap-5 px-4 py-5 lg:grid-cols-[minmax(0,35fr)_minmax(0,65fr)] lg:items-start lg:gap-6 lg:py-6">
          <aside>
            <InputPanel
              raw={raw} fields={fields} onChange={onChange}
              advancedOpen={advancedOpen} onAdvancedOpen={setAdvancedOpen}
              targets={targets}
              onToggleTarget={(v) => { invalidate(); setTargets((prev) => { const next = new Set(prev); if (!next.delete(v)) next.add(v); return next; }); }}
              onTargets={(list) => { invalidate(); setTargets(new Set(list)); }}
              onExample={loadExample}
              onSolve={runSolve} loading={loading} hasInvalid={hasInvalid}
            />
          </aside>
          <div className="min-w-0 space-y-5">
            <TriangleView
              state={visualState(result?.response ?? null, stale)}
              facts={result?.response.facts ?? {}}
              given={result?.given ?? new Set()}
              highlight={highlight}
              onSelect={(v) => selectResult(selected === v ? null : v)}
              onResetView={clearSelection}
            />
            <ResultsPanel
              result={result} stale={stale} error={error} onRetry={() => runSolve(lastMode.current)}
              selected={selected} onSelect={selectResult}
              selectedStep={selectedStep} onSelectStep={setSelectedStep}
              stepsOpen={stepsOpen} onStepsOpen={setStepsOpen}
              stepView={stepView} onStepView={setStepView}
            />
          </div>
        </main>
      </div>
    </TooltipProvider>
  );
}
