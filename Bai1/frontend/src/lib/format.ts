/** Display-only rounding; the underlying value is never modified. */
export function formatValue(value: number): string {
  if (value !== 0 && Math.abs(value) < 1e-3) return value.toPrecision(4);
  return String(Number(value.toFixed(4)));
}

/** Make backend formula strings readable. Display only: nothing evaluates them. */
export function prettyFormula(formula: string): string {
  return formula
    .replace(/acos_deg/g, "arccos")
    .replace(/sin_deg/g, "sin")
    .replace(/cos_deg/g, "cos")
    .replace(/sqrt/g, "√")
    .replace(/\^2/g, "²")
    .replace(/\*/g, "·");
}
