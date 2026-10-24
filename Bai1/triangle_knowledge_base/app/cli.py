"""Terminal adapter; parsing and presentation only, all solving uses the service."""
import argparse
from collections.abc import Sequence

from .models import SolveResponse, SolveStatus
from .services.solver_service import SolverService


def parse_facts(text: str) -> dict[str, float]:
    """Parse comma-separated assignments without evaluating expressions."""
    facts: dict[str, float] = {}
    if not text.strip():
        return facts
    for item in text.split(","):
        key, separator, raw = item.partition("=")
        key = key.strip()
        if not separator or not key or not raw.strip():
            raise ValueError(f"Expected variable=number, received {item!r}")
        if key in facts:
            raise ValueError(f"Duplicate fact: {key}")
        try:
            facts[key] = float(raw)
        except ValueError as error:
            raise ValueError(f"{key}: expected a number, received {raw!r}") from error
    return facts


def display(response: SolveResponse) -> str:
    """Round only displayed text; JSON retains full numerical precision."""
    lines = [response.status.value, response.message, "Facts:"]
    lines.extend(f"  {v.value} = {value:.10g}" for v, value in response.facts.items())
    trace = response.relevant_trace if response.relevant_trace is not None else response.trace
    if trace:
        lines.append("Relevant inference trace:" if response.relevant_trace is not None else "Inference trace:")
        for step in trace:
            inputs = ", ".join(f"{v.value}={x:.10g}" for v, x in step.inputs.items())
            lines.append(f"  {step.step}. {step.rule_id} [{step.group}] {step.formula}; "
                         f"inputs: {inputs} -> {step.output.value}={step.value:.10g}")
    if response.missing:
        lines.append("Missing goals: " + ", ".join(v.value for v in response.missing))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run one solve request. Exit 0=solved, 1=unresolved, 2=invalid/conflicting."""
    parser = argparse.ArgumentParser(description="Triangle computational network (angles in degrees)")
    parser.add_argument("--facts", required=True, help="e.g. a=3,b=4,c=5")
    parser.add_argument("--goals", required=True, help="e.g. p,S,hc,r,R")
    parser.add_argument("--json", action="store_true", help="Print the complete JSON response")
    parser.add_argument("--trace-for", help="Show the dependency steps for these variables, e.g. hc,r")
    args = parser.parse_args(argv)
    try:
        request = {"facts": parse_facts(args.facts),
                   "goals": [v.strip() for v in args.goals.split(",") if v.strip()]}
        if args.trace_for is not None:
            request["trace_targets"] = [v.strip() for v in args.trace_for.split(",") if v.strip()]
        response = SolverService().solve(request)
    except ValueError as error:
        response = SolveResponse(status=SolveStatus.INVALID, message=str(error), reason_code="INVALID_INPUT",
                                 diagnostics=[{"code": "INVALID_INPUT", "message": str(error)}],
                                 stats={"steps": 0, "time_ms": 0, "termination_reason": "INVALID_INPUT"})
    print(response.model_dump_json(indent=2) if args.json else display(response))
    return 0 if response.status == SolveStatus.SOLVED else 1 if response.status == SolveStatus.UNRESOLVED else 2
