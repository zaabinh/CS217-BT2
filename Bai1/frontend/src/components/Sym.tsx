import type { Variable } from "@/lib/variables";

/** Renders a variable in math notation: ha → h with subscript a. */
export function Sym({ v }: { v: Variable }) {
  return v.length === 2
    ? <span className="font-math italic">{v[0]}<sub className="text-[0.7em]">{v[1]}</sub></span>
    : <span className="font-math italic">{v}</span>;
}
