"""Geometric domain validation and redundant-fact consistency checks."""
import math
from collections.abc import Mapping
from itertools import combinations

from ..knowledge.formulas import heron
from ..knowledge.rules import RuleRegistry
from ..models import SolveStatus, Variable


class TriangleError(Exception):
    """A proven domain error or a contradiction, with a business status."""

    def __init__(self, status: SolveStatus, message: str, reason_code: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.reason_code = reason_code or ("INVALID_INPUT" if status == SolveStatus.INVALID else "CONFLICTING_FACTS")


class TriangleValidator:
    """Validate only constraints supported by the current set of facts."""

    def __init__(self, registry: RuleRegistry, *, abs_tol: float = 1e-8,
                 rel_tol: float = 1e-7) -> None:
        if not all(math.isfinite(t) and t >= 0 for t in (abs_tol, rel_tol)):
            raise ValueError("Tolerances must be finite and nonnegative")
        self.registry = registry
        self.abs_tol = abs_tol
        self.rel_tol = rel_tol

    def close(self, actual: float, expected: float) -> bool:
        return math.isclose(actual, expected, abs_tol=self.abs_tol, rel_tol=self.rel_tol)

    @staticmethod
    def valid_value(variable: Variable, value: float) -> bool:
        return (math.isfinite(value) and value > 0
                and (variable not in (Variable.A, Variable.B, Variable.C) or value < 180))

    def compare(self, label: str, variable: Variable, actual: float, expected: float) -> None:
        if not self.close(actual, expected):
            raise TriangleError(SolveStatus.INCONSISTENT,
                                f"{label}: {variable.value}={actual:.16g}, expected {expected:.16g}")

    def validate(self, facts: Mapping[Variable, float]) -> None:
        """Raise TriangleError for a demonstrated violation; never mutate facts."""
        for var, value in facts.items():
            if not self.valid_value(var, value):
                raise TriangleError(SolveStatus.INVALID, f"{var.value}={value}: outside its domain")

        if Variable.p in facts:
            for side in (Variable.a, Variable.b, Variable.c):
                if side in facts and facts[Variable.p] <= facts[side]:
                    raise TriangleError(SolveStatus.INCONSISTENT,
                                        f"Q02: p must exceed {side.value} in a nondegenerate triangle")

        sides = (Variable.a, Variable.b, Variable.c)
        if all(var in facts for var in sides):
            a, b, c = (facts[var] for var in sides)
            x, y, z = sorted((a, b, c))
            # x > z-y avoids overflow in x+y and accepts strictly valid thin triangles.
            if x <= z-y:
                raise TriangleError(SolveStatus.INVALID, "Triangle inequality violated (possibly degenerate)", "INVALID_TRIANGLE")
            p = a/2+b/2+c/2
            if Variable.p in facts:
                self.compare("Q02/R04", Variable.p, facts[Variable.p], p)
            if Variable.S in facts:
                try:
                    area = heron(p, a, b, c)
                except (ArithmeticError, ValueError):
                    area = math.nan
                if math.isfinite(area) and area > 0:
                    self.compare("Q05/R20 Heron", Variable.S, facts[Variable.S], area)

        angles = [facts[var] for var in (Variable.A, Variable.B, Variable.C) if var in facts]
        if len(angles) == 3 and not self.close(sum(angles), 180):
            raise TriangleError(SolveStatus.INCONSISTENT, "Q01: A+B+C must equal 180 degrees")
        if any(x+y >= 180 for x, y in combinations(angles, 2)):
            raise TriangleError(SolveStatus.INCONSISTENT, "Q01: two angles must sum to less than 180 degrees")

        for rule in self.registry:
            if rule.output not in facts or not all(v in facts for v in rule.inputs):
                continue
            try:
                expected = self.registry.calculate(rule.id, facts)
            except (ArithmeticError, ValueError):
                # A failed floating-point evaluation is not proof of a contradiction.
                # The engine reports numerical limitations if they prevent a derivation.
                continue
            if not self.valid_value(rule.output, expected):
                continue
            self.compare(f"{rule.group}/{rule.id}", rule.output, facts[rule.output], expected)
