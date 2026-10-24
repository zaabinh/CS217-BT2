"""
Kiểm thử tự động. Chạy:  python -m pytest -v 
"""
import pytest

from formula import FormulaError, atom_balance, molar_mass, parse_formula  # noqa: E402
from inference import (astar_optimal, closure, forward_chaining, good_solution,  # noqa: E402
                       is_solution, solve)
from knowledge_base import KnowledgeBase  # noqa: E402
from matcher import Matcher  # noqa: E402
from testing import load_cases, run_case  # noqa: E402

KB = KnowledgeBase()
CASES = load_cases()


# ---------------------------------------------------------------- test case của bài toán
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case):
    out = run_case(KB, case)
    failed = [label for label, ok in out["checks"] if not ok]
    assert out["passed"], f"{case['id']} sai: {failed}"


# ---------------------------------------------------------------- cơ sở tri thức
def test_kb_size():
    assert len(KB.reactions) == 94
    assert len(KB.chemicals) >= 80


def test_all_reactions_balanced():
    for r in KB.reactions:
        ok, left, right = atom_balance(r.reactants, r.products, r.weights)
        assert ok, f"{r.id} chưa cân bằng: {left} != {right}"


def test_consistency_has_no_error():
    errors = [i for i in KB.check_consistency() if i["level"] == "Lỗi"]
    assert errors == []


# ---------------------------------------------------------------- công thức hóa học
def test_parse_formula():
    assert dict(parse_formula("Al2(SO4)3")) == {"Al": 2, "S": 3, "O": 12}
    assert dict(parse_formula("Ca(OH)2")) == {"Ca": 1, "O": 2, "H": 2}
    assert dict(parse_formula("H₂SO₄")) == {"H": 2, "S": 1, "O": 4}
    for bad in ["Xy2", "H2(SO4", "2H2O", "h2so4", ""]:
        with pytest.raises(FormulaError):
            parse_formula(bad)


def test_molar_mass():
    assert round(molar_mass("H2SO4", KB.atomic_masses())) == 98


# ---------------------------------------------------------------- so khớp
def test_matcher():
    m = Matcher(KB)
    assert m.parse("h2so4, muối ăn, Axit Sunfuric").formulas == ["H2SO4", "NaCl"]
    assert m.parse("S H2O NaCl").formulas == ["S", "H2O", "NaCl"]
    res = m.parse("H2SO")
    assert not res.ok and "H2SO4" in res.errors[0].suggestions


# ---------------------------------------------------------------- thuật toán
H = ["S", "H2O", "NaCl"]
G = ["Na2SO4", "H2SO4", "HCl", "Na"]


def test_closure_contains_goal():
    clo, _ = closure(H, KB.reactions)
    assert set(G) <= clo


def test_good_solution_is_minimal():
    sol, _ = forward_chaining(H, G, KB.reactions)
    good = good_solution(H, G, sol)
    assert is_solution(H, G, good)
    for i in range(len(good)):   # bỏ bất kỳ bước nào cũng không còn là lời giải
        assert not is_solution(H, G, good[:i] + good[i + 1:])


def _uniform_cost(H, G, rules):
    """Tìm kiếm chi phí đều (A* với h = 0) để đối chiếu tính tối ưu của A*."""
    import heapq
    import itertools
    start, G = frozenset(H), frozenset(G)
    cnt = itertools.count()
    pq, best = [(0, next(cnt), start)], {start: 0}
    while pq:
        g, _, N = heapq.heappop(pq)
        if G <= N:
            return g
        if g > best.get(N, 1e9):
            continue
        for r in rules:
            if r.hyp <= N and not r.goal <= N:
                S = N | r.goal
                if g + r.cost < best.get(S, 1e9):
                    best[S] = g + r.cost
                    heapq.heappush(pq, (g + r.cost, next(cnt), S))
    return None


@pytest.mark.parametrize("h,g", [
    (["S", "H2O"], ["H2SO4"]),
    (["Fe", "HCl", "MnO2"], ["FeCl3"]),
    (["NaCl", "H2O"], ["HCl", "NaOH"]),
    (["S", "H2O", "NaCl"], ["Na2SO4"]),
])
def test_astar_is_optimal(h, g):
    from inference import relevant_rules
    rules = relevant_rules(h, g, KB.reactions)
    path, _, _ = astar_optimal(h, g, KB.reactions)
    assert is_solution(h, g, path)
    assert sum(r.cost for r in path) == _uniform_cost(h, g, rules)


def test_backward_solution_valid():
    res = solve(KB, H, G, "backward")
    assert res.solvable and is_solution(H, G, res.solution)


def test_condition_filter():
    res = solve(KB, H, G, "good", enabled_tags=set())
    assert not res.solvable and res.suggestions


# ---------------------------------------------------------------- cập nhật CSTT (trên bản sao)
def test_kb_update(tmp_path):
    import shutil
    from knowledge_base import DATA_DIR, Reaction
    for name in ("chemicals.json", "reactions.json"):
        shutil.copy(DATA_DIR / name, tmp_path / name)
    kb = KnowledgeBase(tmp_path)
    bad = Reaction(id="R95", reactants=["Zn", "Cl2"], products=["ZnCl2"], weights=[2, 1, 1])
    assert any("chưa cân bằng" in e for e in kb.add_reaction(bad))
    dup = Reaction(id="R95", reactants=["Na", "Cl2"], products=["NaCl"], weights=[2, 1, 2],
                   condition_tags=["t"])
    assert any("Trùng" in e for e in kb.add_reaction(dup))
    good = Reaction(id="R95", reactants=["Zn", "Cl2"], products=["ZnCl2"], weights=[1, 1, 1],
                    condition_tags=["t"], cost=2)
    assert kb.add_reaction(good) == []
    assert len(KnowledgeBase(tmp_path).reactions) == 95       # đã ghi xuống file
    assert kb.delete_chemical("Zn")                            # đang dùng -> không xóa được
    kb.delete_reaction("R95")
    assert len(KnowledgeBase(tmp_path).reactions) == 94
