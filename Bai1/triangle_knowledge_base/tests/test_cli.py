import json
import subprocess
import sys
from pathlib import Path
import pytest

from triangle_knowledge_base.app.cli import main
from triangle_knowledge_base.app.services.solver_service import SolverService

BAI1 = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("facts,goals,status,code", [
    ("a=3,b=4,c=5", "p,S,hc,r,R", "SOLVED", 0),
    ("a=3,b=4,p=6", "c,S,hc", "SOLVED", 0),
    ("a=3", "S", "UNRESOLVED", 1),
    ("a=3,b=4,c=5,S=7", "S", "INCONSISTENT", 2),
    ("a=-3", "S", "INVALID", 2),
])
def test_cli_subprocess(facts, goals, status, code):
    process = subprocess.run([sys.executable, "main.py", "--facts", facts, "--goals", goals, "--json"],
                             cwd=BAI1, capture_output=True, text=True, timeout=15)
    assert process.returncode == code, process.stderr
    response = json.loads(process.stdout)
    assert response["status"] == status
    assert set(response) == {"status", "facts", "missing", "trace", "message", "reason_code", "diagnostics", "stats", "relevant_trace"}


@pytest.mark.parametrize("facts,goals", [
    ("a", "S"), ("a=x", "S"), ("a=3,a=4", "S"),
    ("a=nan", "S"), ("a=inf", "S"), ("a=True", "S"),
    ("unknown=2", "S"), ("a=3", ""), ("a=3", "unknown"),
])
def test_cli_errors(capsys, facts, goals):
    assert main(["--facts", facts, "--goals", goals, "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "INVALID"


def test_module_entry_point_and_json_matches_service():
    process = subprocess.run([sys.executable, "-m", "triangle_knowledge_base", "--facts", "S=6,p=6",
                              "--goals", "r", "--json"], cwd=BAI1, capture_output=True, text=True, timeout=15)
    assert process.returncode == 0
    expected = SolverService().solve({"facts": {"S": 6, "p": 6}, "goals": ["r"]})
    response = json.loads(process.stdout)
    response["stats"].pop("time_ms")
    assert response == expected.model_dump(mode="json", exclude={"stats": {"time_ms"}})


def test_text_trace(capsys):
    assert main(["--facts", "c=10,hc=6", "--goals", "S"]) == 0
    text = capsys.readouterr().out
    assert "SOLVED" in text and "R27 [Q06]" in text and "S=30" in text
