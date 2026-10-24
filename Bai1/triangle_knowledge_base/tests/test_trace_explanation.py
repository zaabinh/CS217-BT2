import json
import pytest
from fastapi.testclient import TestClient

from triangle_knowledge_base.app.api.main import create_app
from triangle_knowledge_base.app.cli import main
from triangle_knowledge_base.app.services.solver_service import SolverService

FACTS = {"a": 3, "b": 4, "p": 6}


def test_dependency_explanation_preserves_full_trace_and_step_numbers():
    service = SolverService()
    full = service.solve({"facts": FACTS, "goals": ["hc"]})
    filtered = service.solve({"facts": FACTS, "goals": ["hc"], "trace_targets": ["hc"]})
    assert full.relevant_trace is None
    assert filtered.trace == full.trace and filtered.facts == full.facts
    assert [s.rule_id for s in filtered.relevant_trace] == ["R07", "R20", "R28"]
    assert [s.step for s in filtered.relevant_trace] == [1, 5, 8]


@pytest.mark.parametrize("targets,expected", [(["a"], []), (["R"], []), (["hc", "p"], ["R07", "R20", "R28"])])
def test_given_unavailable_and_multiple_targets(targets, expected):
    response = SolverService().solve({"facts": FACTS, "goals": ["hc"], "trace_targets": targets})
    assert [s.rule_id for s in response.relevant_trace] == expected


def test_http_and_cli_expose_the_same_filtered_trace(capsys):
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/solve", json={"facts": FACTS, "goals": ["hc"], "trace_targets": ["hc"]})
        assert response.status_code == 200
        body = response.json()
        assert client.post("/api/v1/solve", json={"facts": FACTS, "goals": ["hc"], "trace_targets": ["unknown"]}).status_code == 422
    assert main(["--facts", "a=3,b=4,p=6", "--goals", "hc", "--trace-for", "hc", "--json"]) == 0
    cli = json.loads(capsys.readouterr().out)
    assert cli["relevant_trace"] == body["relevant_trace"]
    assert cli["trace"] == body["trace"]
    assert main(["--facts", "a=3,b=4,p=6", "--goals", "hc", "--trace-for", "hc"]) == 0
    text = capsys.readouterr().out
    assert "R07" in text and "R20" in text and "R28" in text and "R15" not in text
