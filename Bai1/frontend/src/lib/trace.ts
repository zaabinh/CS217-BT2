import type { InferenceStep } from "./api";
import type { Variable } from "./variables";

/** Steps a target depends on, following each step's recorded inputs back through the trace. */
export function relevantSteps(trace: InferenceStep[], target: Variable): InferenceStep[] {
  const producer = new Map(trace.map((s) => [s.output, s]));
  const needed = new Set<number>();
  const visit = (v: Variable) => {
    const step = producer.get(v);
    if (!step || needed.has(step.step)) return;
    needed.add(step.step);
    (Object.keys(step.inputs) as Variable[]).forEach(visit);
  };
  visit(target);
  return trace.filter((s) => needed.has(s.step));
}
