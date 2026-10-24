import type { Variable } from "./variables";

export type SolveStatus = "SOLVED" | "UNRESOLVED" | "INVALID" | "INCONSISTENT";
export type Facts = Partial<Record<Variable, number>>;

/** Mirrors models/inference.py SolveRequest / InferenceStep / SolveResponse. */
export interface SolveRequest { facts: Facts; goals: Variable[]; trace_targets?: Variable[] }
export interface InferenceStep {
  step: number; rule_id: string; group: string;
  inputs: Facts; output: Variable; value: number; formula: string;
}
export interface SolveResponse {
  status: SolveStatus; facts: Facts; missing: Variable[]; trace: InferenceStep[]; message: string;
    reason_code?: string;
    diagnostics?: Array<Record<string, string>>;
    stats?: Record<string, number | string>;
    relevant_trace?: InferenceStep[] | null;
}

/** Empty base means same origin; in development the Vite proxy forwards /api. */
export const API_BASE_URL: string = import.meta.env?.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(message: string, readonly kind: "network" | "http" | "format", readonly status?: number) {
    super(message);
  }
}

const STATUSES: SolveStatus[] = ["SOLVED", "UNRESOLVED", "INVALID", "INCONSISTENT"];

function isSolveResponse(data: unknown): data is SolveResponse {
  const d = data as SolveResponse;
  return !!d && STATUSES.includes(d.status) && typeof d.facts === "object" && d.facts !== null
    && Array.isArray(d.missing) && Array.isArray(d.trace) && typeof d.message === "string";
}

export async function solve(request: SolveRequest, signal?: AbortSignal, base = API_BASE_URL): Promise<SolveResponse> {
  let response: Response;
  try {
    response = await fetch(`${base}/api/v1/solve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    });
  } catch (error) {
    if ((error as Error).name === "AbortError") throw error;
    throw new ApiError("Cannot reach the solver backend. Make sure the FastAPI server is running, then try again.", "network");
  }
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(`The server returned an unreadable response (HTTP ${response.status}).`, "format", response.status);
  }
  if (!response.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    const text = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
      : typeof detail === "string" ? detail : "";
    throw new ApiError(`The server rejected the request (HTTP ${response.status})${text ? `: ${text}` : "."}`, "http", response.status);
  }
  if (!isSolveResponse(data)) throw new ApiError("The server returned an unexpected response format.", "format", response.status);
  return data;
}
