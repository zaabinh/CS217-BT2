"""Report T01–T12 and monotonic forward-chaining invariants."""
import math
import pytest

from triangle_knowledge_base.app.models import SolveResponse, SolveStatus, Variable
from triangle_knowledge_base.app.services.solver_service import SolverService

CASES = [
    ({"a": 3, "b": 4, "c": 5}, ["p", "S", "hc", "r", "R"], "SOLVED", {"p": 6, "S": 6, "hc": 2.4, "r": 1, "R": 2.5}),
    ({"A": 50, "B": 60, "c": 10}, ["C", "a", "b"], "SOLVED", {"C": 70, "a": 10*math.sin(math.radians(50))/math.sin(math.radians(70)), "b": 10*math.sin(math.radians(60))/math.sin(math.radians(70))}),
    ({"b": 3, "c": 4, "A": 90}, ["a", "S"], "SOLVED", {"a": 5, "S": 6}),
    ({"a": 3, "b": 4, "p": 6}, ["c", "S", "hc"], "SOLVED", {"c": 5, "S": 6, "hc": 2.4}),
    ({"c": 10, "hc": 6}, ["S"], "SOLVED", {"S": 30}),
    ({"a": 3}, ["S"], "UNRESOLVED", {}),
    ({"a": 1, "b": 2, "c": 3}, ["S"], "INVALID", {}),
    ({"a": -3, "b": 4, "c": 5}, ["S"], "INVALID", {}),
    ({"a": 3, "b": 4, "c": 5, "S": 7}, ["S"], "INCONSISTENT", {}),
    ({"A": 30, "B": 60, "C": 90}, ["a"], "UNRESOLVED", {}),
    ({"A": 30, "a": 5, "b": 8}, ["B", "C", "c"], "UNRESOLVED", {}),
    ({"S": 6, "p": 6}, ["r"], "SOLVED", {"r": 1}),
]


def assert_trace(service, original, response):
    known = dict(original)
    for index, step in enumerate(response.trace, 1):
        rule = service.registry.get(step.rule_id)
        assert step.step == index
        assert step.group == rule.group
        assert step.formula == rule.formula
        assert step.output == rule.output
        assert set(step.inputs) == set(rule.inputs)
        assert all(v in known and known[v] == x for v, x in step.inputs.items())
        assert step.output not in known
        assert step.value == service.registry.calculate(rule.id, known)
        known[step.output] = step.value
    assert known == response.facts
    assert len(response.trace) <= 13-len(original)


@pytest.mark.parametrize("facts,goals,status,expected", CASES, ids=[f"T{i:02}" for i in range(1, 13)])
def test_report_cases(facts, goals, status, expected):
    service = SolverService()
    original = dict(facts)
    response = service.solve({"facts": facts, "goals": goals})
    assert response.status == status, response.message
    assert facts == original
    assert all(response.facts[k] == v for k, v in original.items())
    assert set(response.missing) == set(goals)-set(response.facts)
    for key, value in expected.items():
        assert response.facts[key] == pytest.approx(value, abs=1e-8, rel=1e-7)
    assert_trace(service, original, response)
    if status == "SOLVED" and set(goals)-set(original):
        assert response.trace
    assert SolveResponse.model_validate_json(response.model_dump_json()) == response


def test_deterministic_scan_and_request_isolation():
    service = SolverService()
    payload = {"facts": {"a": 3, "b": 4, "p": 6}, "goals": ["c", "S", "hc"]}
    first = service.solve(payload)
    assert [s.rule_id for s in first.trace] == ["R07", "R15", "R17", "R19", "R20", "R22", "R25", "R28"]
    assert first == service.solve(payload)
    assert service.solve({"facts": {"a": 3}, "goals": ["S"]}).facts == {"a": 3}


def test_already_known_goal_still_validated():
    service = SolverService()
    good = service.solve({"facts": {"S": 6}, "goals": ["S"]})
    assert good.status == "SOLVED" and good.trace == []
    bad = service.solve({"facts": {"a": 3, "b": 4, "c": 5, "S": 7}, "goals": ["S"]})
    assert bad.status == "INCONSISTENT"
    assert bad.facts["S"] == 7 and not bad.trace
    assert "R20" in bad.message and "6" in bad.message


def test_conflicting_candidate_never_enters_knowledge():
    response = SolverService().solve({"facts": {"a": 3, "ha": 4, "b": 4, "hb": 4}, "goals": ["S"]})
    assert response.status == "INCONSISTENT"
    assert "R21" in response.message and "R24" in response.message
    assert "S" not in response.facts and not response.trace
    assert response.missing == [Variable.S]


def test_multiple_consistent_paths():
    response = SolverService().solve({"facts": {"a": 3, "ha": 4, "b": 4, "hb": 3}, "goals": ["S"]})
    assert response.status == "SOLVED"
    assert response.facts["S"] == 6
    assert [s.rule_id for s in response.trace] == ["R21"]


def test_full_closure_has_trace_for_every_new_variable():
    service = SolverService()
    response = service.solve({"facts": {"a": 3, "b": 4, "c": 5}, "goals": list(Variable)})
    assert response.status == SolveStatus.SOLVED
    assert len(response.facts) == 13 and len(response.trace) == 10
    assert_trace(service, {"a": 3, "b": 4, "c": 5}, response)
