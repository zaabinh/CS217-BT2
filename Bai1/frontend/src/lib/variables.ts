/** Mirrors the backend Variable enum (models/triangle.py), in canonical order. */
export const VARIABLES = ["a", "b", "c", "A", "B", "C", "ha", "hb", "hc", "S", "p", "r", "R"] as const;
export type Variable = (typeof VARIABLES)[number];

export const BASIC_SIDES: Variable[] = ["a", "b", "c"];
export const BASIC_ANGLES: Variable[] = ["A", "B", "C"];
export const ADVANCED: Variable[] = ["S", "p", "ha", "hb", "hc", "r", "R"];

export const VARIABLE_NAMES: Record<Variable, string> = {
  a: "Side a", b: "Side b", c: "Side c",
  A: "Angle A", B: "Angle B", C: "Angle C",
  ha: "Altitude to a", hb: "Altitude to b", hc: "Altitude to c",
  S: "Area", p: "Semiperimeter", r: "Inradius", R: "Circumradius",
};

export const isAngle = (v: Variable) => v === "A" || v === "B" || v === "C";
export const isSide = (v: Variable) => v === "a" || v === "b" || v === "c";
export const unitOf = (v: Variable) => (isAngle(v) ? "°" : "");

/** Display names for the backend relation groups Q01–Q10 (see IMPLEMENTATION_GUIDE.md). */
export const GROUP_NAMES: Record<string, string> = {
  Q01: "Angle sum",
  Q02: "Semiperimeter",
  Q03: "Law of sines",
  Q04: "Law of cosines",
  Q05: "Heron's formula",
  Q06: "Area from side and altitude",
  Q07: "Area from two sides and included angle",
  Q08: "Inradius",
  Q09: "Area and circumradius",
  Q10: "Side, angle and circumradius",
};
