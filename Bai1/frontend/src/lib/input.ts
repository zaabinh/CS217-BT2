import { isAngle, isSide, VARIABLES, type Variable } from "./variables";

export type RawInputs = Partial<Record<Variable, string>>;
export type FieldState =
  | { kind: "empty" }
  | { kind: "invalid"; message: string }
  | { kind: "valid"; value: number };

const NUMBER = /^[+-]?(\d+(\.\d*)?|\.\d+)(e[+-]?\d+)?$/i;

/** Parse one field; a comma is accepted as decimal separator. Empty never becomes 0. */
export function parseField(variable: Variable, raw: string | undefined): FieldState {
  const text = (raw ?? "").trim().replace(",", ".");
  if (text === "") return { kind: "empty" };
  if (!NUMBER.test(text)) return { kind: "invalid", message: "Enter a number, e.g. 3 or 4.5." };
  const value = Number(text);
  if (!Number.isFinite(value)) return { kind: "invalid", message: "This number is too large." };
  if (isAngle(variable)) {
    if (value <= 0 || value >= 180) return { kind: "invalid", message: "Angles must be between 0° and 180°." };
  } else if (value <= 0) {
    return { kind: "invalid", message: isSide(variable) ? "Side lengths must be greater than zero." : "Value must be greater than zero." };
  }
  return { kind: "valid", value };
}

export function parseAll(raw: RawInputs): Record<Variable, FieldState> {
  return Object.fromEntries(VARIABLES.map((v) => [v, parseField(v, raw[v])])) as Record<Variable, FieldState>;
}

/** Only populated fields; null when any field is invalid so no bad request is sent. */
export function buildFacts(raw: RawInputs): Partial<Record<Variable, number>> | null {
  const facts: Partial<Record<Variable, number>> = {};
  for (const [v, state] of Object.entries(parseAll(raw)) as [Variable, FieldState][]) {
    if (state.kind === "invalid") return null;
    if (state.kind === "valid") facts[v] = state.value;
  }
  return facts;
}
