import pytest

from triangle_knowledge_base.app.services.solver_service import SolverService


@pytest.mark.parametrize("facts,goals,status,code", [
    ({"a": 3, "b": 4, "c": 5}, ["S"], "SOLVED", "GOALS_REACHED"),
    ({"S": 6}, ["S"], "SOLVED", "GOALS_ALREADY_KNOWN"),
    ({"a": 3}, ["S"], "UNRESOLVED", "INSUFFICIENT_FACTS"),
    ({"a": True}, ["S"], "INVALID", "INVALID_INPUT"),
    ({"a": 1, "b": 2, "c": 3}, ["S"], "INVALID", "INVALID_TRIANGLE"),
    ({"a": 3, "b": 4, "c": 5, "S": 7}, ["S"], "INCONSISTENT", "CONFLICTING_FACTS"),
    ({"c": 1e300, "hc": 1e300}, ["S"], "UNRESOLVED", "NUMERICAL_LIMIT_REACHED"),
])
def test_reason_codes_and_diagnostics(facts, goals, status, code):
    result = SolverService().solve({"facts": facts, "goals": goals})
    assert result.status == status and result.reason_code == code
    assert result.stats["termination_reason"] == code
    assert result.stats["steps"] == len(result.trace)
    if status in ("INVALID", "INCONSISTENT") or code == "NUMERICAL_LIMIT_REACHED":
        assert result.diagnostics and result.diagnostics[0]["code"] == code
