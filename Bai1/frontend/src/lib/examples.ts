import type { RawInputs } from "./input";
import type { Variable } from "./variables";

export interface Example { id: string; label: string; inputs: RawInputs; targets: Variable[] }

export const EXAMPLES: Example[] = [
  { id: "345", label: "3-4-5 triangle (SSS)", inputs: { a: "3", b: "4", c: "5" }, targets: ["S", "hc", "R"] },
  { id: "sas", label: "SAS: b = 3, c = 4, A = 90°", inputs: { b: "3", c: "4", A: "90" }, targets: ["a", "S"] },
  { id: "asa", label: "ASA/AAS: A = 50°, B = 60°, c = 10", inputs: { A: "50", B: "60", c: "10" }, targets: ["C", "a", "b"] },
  { id: "insufficient", label: "Insufficient information: a = 3", inputs: { a: "3" }, targets: ["S"] },
  { id: "invalid", label: "Invalid triangle: 1, 2, 3", inputs: { a: "1", b: "2", c: "3" }, targets: ["S"] },
];
