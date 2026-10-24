import pytest
from fastapi.testclient import TestClient

from triangle_knowledge_base.app.api.main import create_app
from triangle_knowledge_base.app.models import SolveResponse, Variable
from triangle_knowledge_base.app.services.solver_service import SolverService


@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client


@pytest.mark.parametrize("facts,goals,status", [
    ({"a": 3, "b": 4, "c": 5}, ["S", "r"], "SOLVED"),
    ({"a": 3}, ["S"], "UNRESOLVED"),
    ({"a": -3}, ["S"], "INVALID"),
    ({"a": 3, "b": 4, "c": 5, "S": 7}, ["S"], "INCONSISTENT"),
])
def test_http_business_results_match_service(client, facts, goals, status):
    payload = {"facts": facts, "goals": goals}
    response = client.post("/api/v1/solve", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == status
    assert SolveResponse.model_validate(body).model_dump(exclude={"stats": {"time_ms"}}) == SolverService().solve(payload).model_dump(exclude={"stats": {"time_ms"}})
    if status == "SOLVED":
        assert body["facts"]["S"] == pytest.approx(6)
        assert body["facts"]["r"] == pytest.approx(1)
        assert body["trace"][0]["rule_id"] == "R04"
        assert body["trace"][0]["group"] == "Q02"
    if status == "INCONSISTENT":
        assert body["facts"]["S"] == 7 and body["trace"] == []


@pytest.mark.parametrize("payload", [
    {"facts": {"a": True}, "goals": ["S"]},
    {"facts": {"a": "3"}, "goals": ["S"]},
    {"facts": {"unknown": 2}, "goals": ["S"]},
    {"facts": {"a": 3}, "goals": ["unknown"]},
    {"facts": {}, "goals": []},
    {"facts": {}},
    {"facts": [], "goals": ["S"]},
    {"facts": {}, "goals": ["S"], "unexpected": 1},
])
def test_http_structural_errors(client, payload):
    response = client.post("/api/v1/solve", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_http_nonfinite_json_returns_422_not_500(client, number):
    response = client.post("/api/v1/solve", content='{"facts":{"a":'+number+'},"goals":["S"]}',
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["detail"]


def test_bad_json(client):
    response = client.post("/api/v1/solve", content="{", headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_metadata_and_openapi(client):
    variables = client.get("/api/v1/variables")
    assert variables.status_code == 200
    data = variables.json()
    assert [v["name"] for v in data] == [v.value for v in Variable]
    assert next(v for v in data if v["name"] == "A")["unit"] == "degrees"
    rules = client.get("/api/v1/rules")
    assert rules.status_code == 200
    assert len(rules.json()) == 46
    assert [r["id"] for r in rules.json()] == [f"R{i:02}" for i in range(1, 47)]
    for row in rules.json():
        assert client.get(f'/api/v1/rules/{row["id"]}').json() == row
        assert set(row) == {"id", "group", "inputs", "output", "formula"}
    assert client.get("/api/v1/rules/R47").status_code == 404
    assert client.get("/api/v1/rules/r01").status_code == 404
    schema = client.get("/openapi.json").json()
    assert set(schema["paths"]) == {"/api/v1/solve", "/api/v1/variables", "/api/v1/rules", "/api/v1/rules/{id}"}
    assert "422" in schema["paths"]["/api/v1/solve"]["post"]["responses"]
    assert client.get("/docs").status_code == 200


def test_routes_use_injected_service():
    class RecordingService(SolverService):
        calls = 0

        def solve(self, request):
            self.calls += 1
            return super().solve(request)

    service = RecordingService()
    with TestClient(create_app(service)) as client:
        assert client.post("/api/v1/solve", json={"facts": {"S": 6, "p": 6}, "goals": ["r"]}).status_code == 200
    assert service.calls == 1
