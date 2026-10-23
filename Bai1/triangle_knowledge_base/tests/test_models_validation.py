import math
import pytest
from pydantic import ValidationError

from triangle_knowledge_base.app.models import SolveRequest, Variable
from triangle_knowledge_base.app.services.solver_service import SolverService
from triangle_knowledge_base.app.knowledge.formulas import acos_deg, cosine_side


@pytest.mark.parametrize("facts,goals", [
    ({"a": True}, ["S"]), ({"a": False}, ["S"]), ({"a": "3"}, ["S"]),
    ({"a": None}, ["S"]), ({"a": float("nan")}, ["S"]),
    ({"a": float("inf")}, ["S"]), ({"a": -float("inf")}, ["S"]),
    ({"a": 10**400}, ["S"]), ({"unknown": 2}, ["S"]),
    ({"Ha": 2}, ["S"]), ({}, ["unknown"]), ({}, []),
])
def test_structural_errors(facts, goals):
    with pytest.raises(ValidationError):
        SolveRequest(facts=facts, goals=goals)
    response = SolverService().solve({"facts": facts, "goals": goals})
    assert response.status == "INVALID"
    assert response.model_dump_json()


def test_numeric_integers_enum_json_and_independent_defaults():
    request = SolveRequest(facts={"a": 3, "A": 60, "r": 1, "R": 2}, goals=["a", "a"])
    assert request.facts[Variable.a] == 3.0 and request.goals == {Variable.a}
    assert SolveRequest.model_validate_json(request.model_dump_json()) == request
    one, two = SolveRequest(goals=["a"]), SolveRequest(goals=["a"])
    one.facts[Variable.a] = 3
    assert two.facts == {}
    with pytest.raises(ValidationError):
        SolveRequest(facts={}, goals=["a"], extra=1)


@pytest.mark.parametrize("facts,status", [
    ({"a": 0}, "INVALID"), ({"ha": -1}, "INVALID"), ({"S": 0}, "INVALID"),
    ({"p": 0}, "INVALID"), ({"r": -2}, "INVALID"), ({"R": 0}, "INVALID"),
    ({"A": 0}, "INVALID"), ({"B": 180}, "INVALID"), ({"C": -1}, "INVALID"),
    ({"a": 1, "b": 1, "c": 3}, "INVALID"),
    ({"A": 100, "B": 90}, "INCONSISTENT"),
    ({"A": 30, "B": 60, "C": 80}, "INCONSISTENT"),
    ({"a": 3, "b": 4, "c": 5, "p": 7}, "INCONSISTENT"),
    ({"a": 3, "b": 4, "c": 5, "A": 40}, "INCONSISTENT"),
    ({"S": 6, "p": 6, "r": 2}, "INCONSISTENT"),
    ({"a": 3, "A": 30, "R": 4}, "INCONSISTENT"),
    ({"p": 1, "b": 2, "c": 2}, "INCONSISTENT"),
])
def test_domain_and_consistency(facts, status):
    response = SolverService().solve({"facts": facts, "goals": [next(iter(facts))]})
    assert response.status == status, response.message
    assert response.facts == facts


def test_tolerance_does_not_overwrite_supplied_value():
    facts = {"a": 3, "b": 4, "c": 5, "S": 6+1e-8}
    response = SolverService().solve({"facts": facts, "goals": ["S"]})
    assert response.status == "SOLVED" and response.facts == facts


def test_arccos_clamps_only_roundoff():
    assert acos_deg(1+1e-14) == 0
    assert acos_deg(-1-1e-14) == 180
    with pytest.raises(ValueError):
        acos_deg(1+1e-8)


@pytest.mark.parametrize("facts,goals", [
    ({"A": 0.001, "B": 89.999, "c": 1}, ["a", "b"]),
    ({"A": 179.9, "B": 0.05, "c": 1}, ["a", "b"]),
    ({"a": 1, "b": 1, "c": 1.999}, ["S"]),
    ({"a": 3e100, "b": 4e100, "c": 5e100}, ["S"]),
])
def test_finite_near_boundary_derivations(facts, goals):
    response = SolverService().solve({"facts": facts, "goals": goals})
    assert response.status == "SOLVED", response.message
    assert all(math.isfinite(x) and x > 0 for x in response.facts.values())


def test_underflow_or_overflow_is_not_declared_invalid():
    for facts in ({"c": 1e-300, "hc": 1e-300}, {"c": 1e300, "hc": 1e300}):
        response = SolverService().solve({"facts": facts, "goals": ["S"]})
        assert response.status == "UNRESOLVED"
        assert response.facts == facts and response.missing == [Variable.S]
        assert "numerical" in response.message


def test_small_included_angle_avoids_cancellation():
    assert cosine_side(1, 1, 1e-8) == pytest.approx(math.radians(1e-8), rel=1e-12)


@pytest.mark.parametrize("short_side", [1e-6, 1e-10, 1e-12])
def test_thin_valid_triangle_is_not_reported_inconsistent(short_side):
    response = SolverService().solve({"facts": {"a": short_side, "b": 1, "c": 1}, "goals": ["S"]})
    assert response.status == "SOLVED", response.message
    expected_area = (short_side/2)*math.sqrt(1-(short_side/2)**2)
    assert response.facts["S"] == pytest.approx(expected_area, rel=1e-7, abs=0)
