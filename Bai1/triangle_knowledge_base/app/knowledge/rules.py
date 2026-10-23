"""The exact directed inventory R01–R46 from Appendix A of the report."""
import math
from collections.abc import Callable, Iterable, Iterator, Mapping

from ..models import Rule, Variable
from .formulas import cosine_angle, cosine_side, heron, sin_deg

Executor = Callable[..., float]


class RuleRegistry:
    """Keep immutable metadata separate from trusted Python executors."""

    def __init__(self, entries: Iterable[tuple[Rule, Executor]]) -> None:
        self._rules: dict[str, Rule] = {}
        self._executors: dict[str, Executor] = {}
        for rule, executor in entries:
            if not isinstance(rule, Rule) or not callable(executor):
                raise ValueError("Registry entries require Rule metadata and a callable")
            if rule.id in self._rules:
                raise ValueError(f"Duplicate rule ID: {rule.id}")
            self._rules[rule.id] = rule
            self._executors[rule.id] = executor
        self._ordered = tuple(self._rules[key] for key in sorted(self._rules))

    def __iter__(self) -> Iterator[Rule]:
        return iter(self._ordered)

    def __len__(self) -> int:
        return len(self._ordered)

    def get(self, rule_id: str) -> Rule:
        return self._rules[rule_id]

    def all(self) -> tuple[Rule, ...]:
        return self._ordered

    def by_group(self, group: str) -> tuple[Rule, ...]:
        return tuple(rule for rule in self if rule.group == group)

    def executor(self, rule_id: str) -> Executor:
        return self._executors[rule_id]

    def calculate(self, rule_id: str, facts: Mapping[Variable, float]) -> float:
        """Evaluate only registered code, never the display formula string."""
        rule = self.get(rule_id)
        value = self.executor(rule_id)(*(facts[var] for var in rule.inputs))
        if not math.isfinite(value):
            raise ArithmeticError(f"{rule_id}: non-finite numerical result")
        return value


def build_registry() -> RuleRegistry:
    """Build an independent inventory in canonical ID order."""
    entries: list[tuple[Rule, Executor]] = []

    def add(group: str, inputs: str, output: str, formula: str, fn: Executor) -> None:
        entries.append((Rule(id=f"R{len(entries)+1:02d}", group=group,
                             inputs=tuple(inputs.split()), output=output, formula=formula), fn))

    add("Q01", "B C", "A", "A = 180 - B - C", lambda B, C: 180-B-C)
    add("Q01", "A C", "B", "B = 180 - A - C", lambda A, C: 180-A-C)
    add("Q01", "A B", "C", "C = 180 - A - B", lambda A, B: 180-A-B)
    add("Q02", "a b c", "p", "p = (a + b + c) / 2", lambda a, b, c: a/2+b/2+c/2)
    add("Q02", "p b c", "a", "a = 2*p - b - c", lambda p, b, c: (p-b)+(p-c))
    add("Q02", "p a c", "b", "b = 2*p - a - c", lambda p, a, c: (p-a)+(p-c))
    add("Q02", "p a b", "c", "c = 2*p - a - b", lambda p, a, b: (p-a)+(p-b))
    add("Q03", "b A B", "a", "a = b*sin_deg(A)/sin_deg(B)", lambda b, A, B: b*(sin_deg(A)/sin_deg(B)))
    add("Q03", "c A C", "a", "a = c*sin_deg(A)/sin_deg(C)", lambda c, A, C: c*(sin_deg(A)/sin_deg(C)))
    add("Q03", "a B A", "b", "b = a*sin_deg(B)/sin_deg(A)", lambda a, B, A: a*(sin_deg(B)/sin_deg(A)))
    add("Q03", "c B C", "b", "b = c*sin_deg(B)/sin_deg(C)", lambda c, B, C: c*(sin_deg(B)/sin_deg(C)))
    add("Q03", "a C A", "c", "c = a*sin_deg(C)/sin_deg(A)", lambda a, C, A: a*(sin_deg(C)/sin_deg(A)))
    add("Q03", "b C B", "c", "c = b*sin_deg(C)/sin_deg(B)", lambda b, C, B: b*(sin_deg(C)/sin_deg(B)))
    add("Q04", "b c A", "a", "a = sqrt(b^2 + c^2 - 2*b*c*cos_deg(A))", cosine_side)
    add("Q04", "a b c", "A", "A = acos_deg((b^2 + c^2 - a^2)/(2*b*c))", cosine_angle)
    add("Q04", "a c B", "b", "b = sqrt(a^2 + c^2 - 2*a*c*cos_deg(B))", cosine_side)
    add("Q04", "a b c", "B", "B = acos_deg((a^2 + c^2 - b^2)/(2*a*c))", lambda a, b, c: cosine_angle(b, a, c))
    add("Q04", "a b C", "c", "c = sqrt(a^2 + b^2 - 2*a*b*cos_deg(C))", cosine_side)
    add("Q04", "a b c", "C", "C = acos_deg((a^2 + b^2 - c^2)/(2*a*b))", lambda a, b, c: cosine_angle(c, a, b))
    add("Q05", "p a b c", "S", "S = sqrt(p*(p-a)*(p-b)*(p-c))", heron)
    add("Q06", "a ha", "S", "S = a*ha/2", lambda a, ha: (a/2)*ha)
    add("Q06", "S a", "ha", "ha = 2*S/a", lambda S, a: 2*(S/a))
    add("Q06", "S ha", "a", "a = 2*S/ha", lambda S, ha: 2*(S/ha))
    add("Q06", "b hb", "S", "S = b*hb/2", lambda b, hb: (b/2)*hb)
    add("Q06", "S b", "hb", "hb = 2*S/b", lambda S, b: 2*(S/b))
    add("Q06", "S hb", "b", "b = 2*S/hb", lambda S, hb: 2*(S/hb))
    add("Q06", "c hc", "S", "S = c*hc/2", lambda c, hc: (c/2)*hc)
    add("Q06", "S c", "hc", "hc = 2*S/c", lambda S, c: 2*(S/c))
    add("Q06", "S hc", "c", "c = 2*S/hc", lambda S, hc: 2*(S/hc))
    add("Q07", "b c A", "S", "S = b*c*sin_deg(A)/2", lambda b, c, A: (b/2)*c*sin_deg(A))
    add("Q07", "a c B", "S", "S = a*c*sin_deg(B)/2", lambda a, c, B: (a/2)*c*sin_deg(B))
    add("Q07", "a b C", "S", "S = a*b*sin_deg(C)/2", lambda a, b, C: (a/2)*b*sin_deg(C))
    add("Q08", "p r", "S", "S = p*r", lambda p, r: p*r)
    add("Q08", "S p", "r", "r = S/p", lambda S, p: S/p)
    add("Q08", "S r", "p", "p = S/r", lambda S, r: S/r)
    add("Q09", "a b c R", "S", "S = a*b*c/(4*R)", lambda a, b, c, R: (a/(4*R))*b*c)
    add("Q09", "a b c S", "R", "R = a*b*c/(4*S)", lambda a, b, c, S: (a/(4*S))*b*c)
    add("Q09", "S R b c", "a", "a = 4*S*R/(b*c)", lambda S, R, b, c: 4*(S/b)*(R/c))
    add("Q09", "S R a c", "b", "b = 4*S*R/(a*c)", lambda S, R, a, c: 4*(S/a)*(R/c))
    add("Q09", "S R a b", "c", "c = 4*S*R/(a*b)", lambda S, R, a, b: 4*(S/a)*(R/b))
    add("Q10", "R A", "a", "a = 2*R*sin_deg(A)", lambda R, A: R*(2*sin_deg(A)))
    add("Q10", "a A", "R", "R = a/(2*sin_deg(A))", lambda a, A: (a/2)/sin_deg(A))
    add("Q10", "R B", "b", "b = 2*R*sin_deg(B)", lambda R, B: R*(2*sin_deg(B)))
    add("Q10", "b B", "R", "R = b/(2*sin_deg(B))", lambda b, B: (b/2)/sin_deg(B))
    add("Q10", "R C", "c", "c = 2*R*sin_deg(C)", lambda R, C: R*(2*sin_deg(C)))
    add("Q10", "c C", "R", "R = c/(2*sin_deg(C))", lambda c, C: (c/2)/sin_deg(C))
    return RuleRegistry(entries)
