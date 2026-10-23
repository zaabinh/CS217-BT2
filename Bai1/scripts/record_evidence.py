"""Run the real test suite and save reproducible report/demo evidence."""
import importlib.metadata
import json
import math
import platform
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from triangle_knowledge_base.app.services.solver_service import SolverService
from triangle_knowledge_base.tests.test_inference import CASES


def main() -> int:
    output = ROOT / "evidence"
    output.mkdir(exist_ok=True)
    test = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)
    (output / "pytest-results.txt").write_text(test.stdout+test.stderr, encoding="utf-8")
    print(test.stdout)
    if test.returncode:
        return test.returncode
    metadata = {
        "recorded_at": datetime.now(timezone(timedelta(hours=7))).isoformat(),
        "timezone": "Asia/Saigon", "python": sys.version, "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name) for name in
                     ("pydantic", "fastapi", "starlette", "uvicorn", "pytest", "httpx")},
        "test_command": "python -m pytest -v", "test_exit_code": test.returncode,
    }
    (output / "environment.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    records = []
    for index, (facts, goals, status, expected) in enumerate(CASES, 1):
        request = {"facts": facts, "goals": goals}
        result = SolverService().solve(request)
        passed = result.status == status and all(
            math.isclose(result.facts[v], x, abs_tol=1e-8, rel_tol=1e-7)
            for v, x in expected.items()
        )
        records.append({"case": f"T{index:02}", "request": request,
                        "expected_status": status, "expected_values": expected,
                        "passed": passed, "response": result.model_dump(mode="json")})
    (output / "report-cases.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    for index in (1, 4, 9, 11):
        facts, goals, _, _ = CASES[index-1]
        args = ["-m", "triangle_knowledge_base", "--facts", ",".join(f"{v}={x}" for v, x in facts.items()),
                "--goals", ",".join(goals)]
        demo = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=15)
        (output / f"demo-T{index:02}.txt").write_text(
            "python "+" ".join(args)+f"\nExit code: {demo.returncode}\n\n"+demo.stdout+demo.stderr,
            encoding="utf-8")
    print(f"Evidence saved to {output}")
    return 0 if all(row["passed"] for row in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
