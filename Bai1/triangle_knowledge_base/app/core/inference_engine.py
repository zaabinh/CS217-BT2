"""Deterministic forward chaining over a separately supplied rule registry."""
from time import perf_counter
from ..knowledge.rules import RuleRegistry
from ..models import InferenceStep, SolveRequest, SolveResponse, SolveStatus, Variable
from .validator import TriangleError, TriangleValidator


class InferenceEngine:
    """Monotonic inference: at most one accepted derivation per unknown variable."""

    def __init__(self, registry: RuleRegistry, validator: TriangleValidator) -> None:
        self.registry = registry
        self.validator = validator

    def solve(self, request: SolveRequest) -> SolveResponse:
        started = perf_counter()
        facts = dict(request.facts)
        trace: list[InferenceStep] = []
        numerical: dict[str, str] = {}

        def result(status: SolveStatus, message: str, reason_code: str) -> SolveResponse:
            diagnostics = [{"code": "NUMERICAL_LIMIT_REACHED", "rule_id": rule, "message": detail}
                           for rule, detail in numerical.items()]
            if status in (SolveStatus.INVALID, SolveStatus.INCONSISTENT):
                diagnostics.append({"code": reason_code, "message": message})
            return SolveResponse(status=status, facts=facts, trace=trace,
                                 missing=[v for v in Variable if v in request.goals and v not in facts],
                                 message=message, reason_code=reason_code, diagnostics=diagnostics,
                                 stats={"steps": len(trace), "known_count": len(facts),
                                        "time_ms": round((perf_counter()-started)*1000, 3),
                                        "termination_reason": reason_code})

        try:
            self.validator.validate(facts)
        except TriangleError as error:
            return result(error.status, str(error), error.reason_code)
        if request.goals.issubset(facts):
            return result(SolveStatus.SOLVED, "All goals were already known; facts passed validation", "GOALS_ALREADY_KNOWN")

        while True:
            changed = False
            for rule in self.registry:
                if rule.output in facts or not all(v in facts for v in rule.inputs):
                    continue
                try:
                    value = self.registry.calculate(rule.id, facts)
                except (ArithmeticError, ValueError) as error:
                    numerical[rule.id] = str(error)
                    continue
                if not self.validator.valid_value(rule.output, value):
                    numerical[rule.id] = "computed value outside the representable domain"
                    continue
                candidate = {**facts, rule.output: value}
                try:
                    self.validator.validate(candidate)
                except TriangleError as error:
                    return result(error.status, f"Candidate from {rule.id} rejected: {error}", error.reason_code)
                trace.append(InferenceStep(step=len(trace)+1, rule_id=rule.id, group=rule.group,
                                           inputs={v: facts[v] for v in rule.inputs}, formula=rule.formula,
                                           output=rule.output, value=value))
                facts = candidate
                changed = True
                if request.goals.issubset(facts):
                    return result(SolveStatus.SOLVED, "All goals derived and facts passed validation", "GOALS_REACHED")
            if not changed:
                message = "Goals cannot be derived from the current 46-rule inventory"
                if numerical:
                    message += "; numerical limits: " + "; ".join(f"{k}: {v}" for k, v in numerical.items())
                return result(SolveStatus.UNRESOLVED, message,
                              "NUMERICAL_LIMIT_REACHED" if numerical else "INSUFFICIENT_FACTS")
