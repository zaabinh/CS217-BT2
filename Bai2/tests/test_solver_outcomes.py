import pytest

from inference import astar_optimal, backward_chaining, closure, solve
from knowledge_base import KnowledgeBase

H = ["S", "H2O", "NaCl"]
G = ["Na2SO4", "H2SO4", "HCl", "Na"]


@pytest.fixture
def kb():
    return KnowledgeBase()


@pytest.mark.parametrize("method,options", [("optimal", {"max_expand": 1}), ("backward", {"max_depth": 0})])
def test_search_limit_does_not_claim_unreachable(kb, method, options):
    result = solve(kb, H, G, method, suggest=False, **options)
    assert not result.solvable and result.goal_reachable is True
    assert result.reason_code == "SEARCH_LIMIT_REACHED"
    assert result.missing == []  # Legacy field: goals outside the closure, not search failure.
    assert "time_ms" in result.stats and result.stats["steps"] == 0


def test_unreachable_is_proven_only_by_closure(kb):
    result = solve(kb, ["S"], ["H2SO4"], suggest=False)
    assert result.goal_reachable is False
    assert result.reason_code == "GOAL_NOT_IN_CLOSURE"
    assert result.missing == ["H2SO4"]


def test_bad_kb_is_rejected_even_if_goal_is_already_known(kb):
    kb.reactions[0].cost = True
    result = solve(kb, ["S"], ["S"])
    assert not result.solvable and result.reason_code == "INVALID_KNOWLEDGE_BASE"
    assert result.goal_reachable is None


@pytest.mark.parametrize("options", [{"method": "bad"}, {"max_expand": True}, {"max_depth": -1}, {"enabled_tags": {"bad"}}])
def test_options_validated_before_already_known_goal(kb, options):
    result = solve(kb, ["S"], ["S"], **options)
    assert not result.solvable and result.reason_code == "INVALID_INPUT"
    assert "time_ms" in result.stats


def test_algorithm_tuple_contracts_remain_unchanged(kb):
    for result in (astar_optimal(H, G, kb.reactions, max_expand=1),
                   backward_chaining(H, G, kb.reactions, max_depth=0)):
        assert len(result) == 3
        assert result[2]["termination_reason"] == "SEARCH_LIMIT_REACHED"
    assert set(G) <= closure(H, kb.reactions)[0]
