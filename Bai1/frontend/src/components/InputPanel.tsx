import { Calculator, ListChecks, Loader2, Sparkles } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Sym } from "@/components/Sym";
import { EXAMPLES } from "@/lib/examples";
import type { FieldState, RawInputs } from "@/lib/input";
import { cn } from "@/lib/utils";
import { ADVANCED, BASIC_ANGLES, BASIC_SIDES, VARIABLE_NAMES, VARIABLES, isAngle, type Variable } from "@/lib/variables";

interface Props {
  raw: RawInputs;
  fields: Record<Variable, FieldState>;
  onChange: (v: Variable, value: string) => void;
  advancedOpen: boolean;
  onAdvancedOpen: (open: boolean) => void;
  targets: Set<Variable>;
  onToggleTarget: (v: Variable) => void;
  onTargets: (targets: Variable[]) => void;
  onExample: (id: string) => void;
  onSolve: (mode: "selected" | "all") => void;
  loading: boolean;
  hasInvalid: boolean;
}

function Field({ v, raw, state, onChange }: { v: Variable; raw?: string; state: FieldState; onChange: Props["onChange"] }) {
  const id = `input-${v}`;
  const invalid = state.kind === "invalid";
  return (
    <div className="min-w-0">
      <label htmlFor={id} className="mb-1 flex items-baseline gap-1 text-sm">
        <Sym v={v} />
        <span className="sr-only">{VARIABLE_NAMES[v]}</span>
        {isAngle(v) && <span className="text-xs text-muted-foreground">(°)</span>}
      </label>
      <Input
        id={id}
        inputMode="decimal"
        autoComplete="off"
        placeholder="—"
        value={raw ?? ""}
        onChange={(e) => onChange(v, e.target.value)}
        aria-invalid={invalid}
        aria-describedby={invalid ? `${id}-error` : undefined}
        aria-label={`${VARIABLE_NAMES[v]}${isAngle(v) ? " in degrees" : ""}`}
      />
      {invalid && <p id={`${id}-error`} className="mt-1 text-xs text-danger">{state.message}</p>}
    </div>
  );
}

export function InputPanel(p: Props) {
  const field = (v: Variable) => <Field key={v} v={v} raw={p.raw[v]} state={p.fields[v]} onChange={p.onChange} />;
  const advancedCount = ADVANCED.filter((v) => p.fields[v].kind !== "empty").length;
  return (
    <Card aria-labelledby="inputs-title">
      <CardHeader>
        <CardTitle id="inputs-title">Known parameters</CardTitle>
        <label className="sr-only" htmlFor="example-select">Load an example problem</label>
        <select
          id="example-select"
          value=""
          onChange={(e) => e.target.value && p.onExample(e.target.value)}
          className="h-9 max-w-[11rem] truncate rounded-md border border-input bg-background px-2 text-xs text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="">Load example…</option>
          {EXAMPLES.map((e) => <option key={e.id} value={e.id}>{e.label}</option>)}
        </select>
      </CardHeader>
      <CardContent className="space-y-4">
        <fieldset>
          <legend className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Sides</legend>
          <div className="grid grid-cols-3 gap-3">{BASIC_SIDES.map(field)}</div>
        </fieldset>
        <fieldset>
          <legend className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Angles</legend>
          <div className="grid grid-cols-3 gap-3">{BASIC_ANGLES.map(field)}</div>
        </fieldset>

        <Accordion type="single" collapsible value={p.advancedOpen ? "advanced" : ""} onValueChange={(v) => p.onAdvancedOpen(v === "advanced")}>
          <AccordionItem value="advanced" className="border-t">
            <AccordionTrigger>
              <span>
                Advanced parameters
                {advancedCount > 0 && <span className="ml-2 text-xs text-muted-foreground">({advancedCount} entered)</span>}
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">{ADVANCED.map(field)}</div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <Separator />

        <fieldset>
          <div className="mb-2 flex items-center justify-between">
            <legend className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Find</legend>
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => p.onTargets([...VARIABLES])}>Select all</Button>
              <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => p.onTargets([])} disabled={p.targets.size === 0}>Clear</Button>
            </div>
          </div>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Target parameters">
            {VARIABLES.map((v) => {
              const on = p.targets.has(v);
              return (
                <Tooltip key={v}>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      aria-pressed={on}
                      aria-label={`Find ${VARIABLE_NAMES[v]}`}
                      onClick={() => p.onToggleTarget(v)}
                      className={cn(
                        "h-9 min-w-11 rounded-full border px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 motion-safe:transition-colors",
                        on ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background hover:border-primary/50 hover:bg-primary/5",
                      )}
                    >
                      <Sym v={v} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>{VARIABLE_NAMES[v]}</TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        </fieldset>

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button className="sm:flex-1" onClick={() => p.onSolve("selected")} disabled={p.loading || p.targets.size === 0 || p.hasInvalid}>
            {p.loading ? <Loader2 className="motion-safe:animate-spin" aria-hidden /> : <Calculator aria-hidden />}
            Solve selected
          </Button>
          <Button variant="outline" className="sm:flex-1" onClick={() => p.onSolve("all")} disabled={p.loading || p.hasInvalid}>
            {p.loading ? <Loader2 className="motion-safe:animate-spin" aria-hidden /> : <Sparkles aria-hidden />}
            Calculate all possible
          </Button>
        </div>
        {p.hasInvalid && (
          <p className="flex items-center gap-1.5 text-xs text-danger"><ListChecks className="size-3.5" aria-hidden />Fix the highlighted fields before solving.</p>
        )}
      </CardContent>
    </Card>
  );
}
