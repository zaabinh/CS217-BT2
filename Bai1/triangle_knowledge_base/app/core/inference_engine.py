"""Deterministic forward chaining over a separately supplied rule registry."""
from ..knowledge.rules import RuleRegistry
from ..models import InferenceStep, SolveRequest, SolveResponse, SolveStatus, Variable
from .validator import TriangleError, TriangleValidator


class InferenceEngine:
    """Monotonic inference: at most one accepted derivation per unknown variable."""

    def __init__(self, registry: RuleRegistry, validator: TriangleValidator) -> None:
        self.registry = registry
        self.validator = validator

    def solve(self, request: SolveRequest) -> SolveResponse:
        facts = dict(request.facts)
        trace: list[InferenceStep] = []
        numerical: dict[str, str] = {}

        def result(status: SolveStatus, message: str) -> SolveResponse:
            return SolveResponse(status=status, facts=facts, trace=trace,
                                 missing=[v for v in Variable if v in request.goals and v not in facts],
                                 message=message)

        try:
            self.validator.validate(facts)
        except TriangleError as error:
            return result(error.status, str(error))
        if request.goals.issubset(facts):
            return result(SolveStatus.SOLVED, "All goals were already known; facts passed validation")

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
                    return result(error.status, f"Candidate from {rule.id} rejected: {error}")
                trace.append(InferenceStep(step=len(trace)+1, rule_id=rule.id, group=rule.group,
                                           inputs={v: facts[v] for v in rule.inputs}, formula=rule.formula,
                                           output=rule.output, value=value))
                facts = candidate
                changed = True
                if request.goals.issubset(facts):
                    return result(SolveStatus.SOLVED, "All goals derived and facts passed validation")
            if not changed:
                message = "Goals cannot be derived from the current 46-rule inventory"
                if numerical:
                    message += "; numerical limits: " + "; ".join(f"{k}: {v}" for k, v in numerical.items())
                return result(SolveStatus.UNRESOLVED, message)
