import type { SolveStatus } from "./api";

export type Tone = "success" | "warning" | "danger";

export const STATUS_UI: Record<SolveStatus, { label: string; tone: Tone }> = {
  SOLVED: { label: "Solved", tone: "success" },
  UNRESOLVED: { label: "Unresolved", tone: "warning" },
  INVALID: { label: "Invalid", tone: "danger" },
  INCONSISTENT: { label: "Inconsistent", tone: "danger" },
};

/** Plain-language version of known backend messages; the raw message stays visible as detail. */
export function explainMessage(status: SolveStatus, message: string, reasonCode?: string): string {
  const reasons: Record<string, string> = {
    INVALID_TRIANGLE: "These side lengths cannot form a valid triangle: the longest side must be shorter than the sum of the other two.",
    INVALID_INPUT: "A value or request is invalid. Check the parameters and selected targets.",
    CONFLICTING_FACTS: "The given facts contradict a relation in the knowledge base.",
    INSUFFICIENT_FACTS: "The current knowledge base cannot derive the remaining values from the available facts. Try adding another known parameter.",
    NUMERICAL_LIMIT_REACHED: "Some values could not be represented accurately. Try using a more suitable unit scale.",
    GOALS_REACHED: "All requested values were derived and passed validation.",
    GOALS_ALREADY_KNOWN: "The requested values were already known and passed validation.",
  };
  if (reasonCode && reasons[reasonCode]) return reasons[reasonCode];
  // Compatibility with older servers and saved responses lacking reason codes.
  if (/Triangle inequality/i.test(message)) return "These side lengths cannot form a valid triangle: the longest side must be shorter than the sum of the other two.";
  if (/outside its domain/i.test(message)) return "A value is outside its allowed range: lengths must be positive and angles between 0° and 180°.";
  if (/A\+B\+C must equal 180/.test(message)) return "The three angles must add up to 180°.";
  if (/two angles must sum to less than 180/.test(message)) return "Any two angles must add up to less than 180°.";
  if (/p must exceed/.test(message)) return "The semiperimeter p must be larger than every side.";
  if (status === "INCONSISTENT") return "The given facts contradict a relation in the knowledge base.";
  if (status === "UNRESOLVED") return "The current knowledge base cannot derive the remaining values from the available facts. Try adding another known parameter.";
  if (status === "SOLVED") return "All requested values were derived and passed validation.";
  return message;
}
