"""
testing.py - Chạy các test case định nghĩa trong data/test_cases.json.
Dùng chung cho pytest (tests/test_cases.py) và tab "Kiểm thử" trên giao diện.
"""
from __future__ import annotations

import json
from pathlib import Path

from inference import METHODS, solve
from knowledge_base import DATA_DIR, KnowledgeBase
from matcher import Matcher


def load_cases(path: Path = DATA_DIR / "test_cases.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_case(kb: KnowledgeBase, case: dict) -> dict:
    """Chạy một test case, trả về dict {passed, checks, result, parse}."""
    m = Matcher(kb)
    ph, pg = m.parse(case["hyp"]), m.parse(case["goal"])
    exp = case["expect"]
    checks: list[tuple[str, bool]] = []
    tags = None if case.get("enabled_tags") is None else set(case["enabled_tags"])

    input_error = (not ph.ok) or (not pg.ok) or not ph.formulas or not pg.formulas
    res = None
    if not input_error:
        res = solve(kb, ph.formulas, pg.formulas, case["method"], tags)

    if "input_error" in exp:
        checks.append(("Phát hiện dữ kiện thiếu / không hợp lệ", input_error == exp["input_error"]))
    if "hyp_formulas" in exp:
        checks.append(("Nhận dạng đúng chất ban đầu", ph.formulas == exp["hyp_formulas"]))
    if "goal_formulas" in exp:
        checks.append(("Nhận dạng đúng chất cần điều chế", pg.formulas == exp["goal_formulas"]))
    if res is not None:
        if "solvable" in exp:
            checks.append((f"Giải được = {exp['solvable']}", res.solvable == exp["solvable"]))
        if res.solvable:
            from inference import is_solution
            checks.append(("Lời giải hợp lệ (D áp dụng được trên H và D(H) ⊇ G)",
                           is_solution(ph.formulas, pg.formulas, res.solution)))
        if "steps" in exp:
            checks.append((f"Số bước = {exp['steps']} (thực tế {len(res.steps)})",
                           len(res.steps) == exp["steps"]))
        if "cost" in exp:
            checks.append((f"Tổng trọng số = {exp['cost']} (thực tế {res.total_cost})",
                           res.total_cost == exp["cost"]))
        if "reactions" in exp:
            got = [r.id for r in res.solution]
            checks.append((f"Các phản ứng = {exp['reactions']} (thực tế {got})",
                           sorted(got) == sorted(exp["reactions"])))
        if "missing" in exp:
            checks.append((f"Chất không điều chế được = {exp['missing']} (thực tế {res.missing})",
                           sorted(res.missing) == sorted(exp["missing"])))
        if "suggestion" in exp:
            checks.append((f"Có gợi ý bổ sung {exp['suggestion']} (thực tế {res.suggestions})",
                           sorted(exp["suggestion"]) in [sorted(s) for s in res.suggestions]))
        if "not_worse_than" in exp:
            other = solve(kb, ph.formulas, pg.formulas, exp["not_worse_than"], tags)
            checks.append((f"Trọng số ≤ {METHODS[exp['not_worse_than']]} "
                           f"({res.total_cost} ≤ {other.total_cost})",
                           res.total_cost <= other.total_cost))
    passed = bool(checks) and all(ok for _, ok in checks)
    return {"passed": passed, "checks": checks, "result": res, "parse": (ph, pg)}


def run_all(kb: KnowledgeBase | None = None) -> list[tuple[dict, dict]]:
    kb = kb or KnowledgeBase()
    return [(c, run_case(kb, c)) for c in load_cases()]


if __name__ == "__main__":
    for case, out in run_all():
        print(f"[{'ĐẠT ' if out['passed'] else 'LỖI'}] {case['id']} - {case['name']}")
        for label, ok in out["checks"]:
            print(f"      {'✔' if ok else '✘'} {label}")
