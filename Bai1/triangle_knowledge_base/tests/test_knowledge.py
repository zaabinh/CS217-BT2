"""Independent Appendix A transcription and numerical checks of every rule."""
import csv
import math
from pathlib import Path
import pytest
from pydantic import ValidationError

from triangle_knowledge_base.app.models import Rule, Variable
from triangle_knowledge_base.app.knowledge.rules import RuleRegistry, build_registry

with Path(__file__).with_name("report_rules.csv").open(encoding="utf-8", newline="") as file:
    REPORT_RULES = list(csv.DictReader(file))


def triangle(a, b, c, area, perimeter):
    return dict(zip(Variable, [
        a, b, c,
        math.degrees(math.acos((b*b+c*c-a*a)/(2*b*c))),
        math.degrees(math.acos((a*a+c*c-b*b)/(2*a*c))),
        math.degrees(math.acos((a*a+b*b-c*c)/(2*a*b))),
        2*area/a, 2*area/b, 2*area/c, area, perimeter,
        area/perimeter, a*b*c/(4*area),
    ]))


def test_inventory_and_groups():
    registry = build_registry()
    assert [v.value for v in Variable] == ["a", "b", "c", "A", "B", "C", "ha", "hb", "hc", "S", "p", "r", "R"]
    assert len(registry) == 46
    assert [r.id for r in registry] == [f"R{i:02}" for i in range(1, 47)]
    assert [len(registry.by_group(f"Q{i:02}")) for i in range(1, 11)] == [3, 4, 6, 6, 1, 9, 3, 3, 5, 6]
    assert registry.all() == tuple(registry)
    with pytest.raises(KeyError):
        registry.get("R47")


@pytest.mark.parametrize("row", REPORT_RULES, ids=[r["id"] for r in REPORT_RULES])
def test_rule_matches_appendix(row):
    rule = build_registry().get(row["id"])
    assert rule.group == row["group"]
    assert tuple(rule.inputs) == tuple(row["inputs"].split())
    assert rule.output == row["output"]
    assert rule.formula == row["formula"]
    assert Rule.model_validate_json(rule.model_dump_json()) == rule
    assert "callable" not in rule.model_dump_json().lower()


@pytest.mark.parametrize("facts", [triangle(3, 4, 5, 6, 6), triangle(13, 14, 15, 84, 21)], ids=["3-4-5", "13-14-15"])
@pytest.mark.parametrize("row", REPORT_RULES, ids=[r["id"] for r in REPORT_RULES])
def test_every_executor(row, facts):
    registry = build_registry()
    inputs = {Variable(v): facts[v] for v in row["inputs"].split()}
    assert registry.calculate(row["id"], inputs) == pytest.approx(facts[row["output"]], abs=1e-8, rel=1e-7)


def test_registry_rejects_duplicates_and_noncallables():
    rule = build_registry().get("R01")
    with pytest.raises(ValueError, match="Duplicate"):
        RuleRegistry([(rule, lambda x, y: 1), (rule, lambda x, y: 2)])
    with pytest.raises(ValueError, match="callable"):
        RuleRegistry([(rule, None)])


@pytest.mark.parametrize("changes", [
    {"id": "R47"}, {"group": "Q11"}, {"inputs": []},
    {"inputs": ["B", "B"]}, {"inputs": ["A", "B"]},
    {"output": "unknown"}, {"formula": ""},
])
def test_invalid_rule_metadata(changes):
    data = build_registry().get("R01").model_dump()
    with pytest.raises(ValidationError):
        Rule.model_validate({**data, **changes})
