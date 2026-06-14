import json
import subprocess
import sys
from pathlib import Path

from config import GENERATED_TESTS_DIR
from graph.state import QAState


def test_runner(state: QAState) -> dict:
    if state.get("error"):
        return {}

    # Derive run_dir from actual test file location (supports cached tests from a prior run)
    run_dir = Path(state["tests"][0]).parent if state.get("tests") else GENERATED_TESTS_DIR / f"run_{state['run_id']}"
    json_report_path = run_dir / "pytest_report.json"

    cmd = [
        sys.executable, "-m", "pytest",
        str(run_dir),
        "--json-report",
        f"--json-report-file={json_report_path}",
        "--tb=short",
        "-v",
        "--no-header",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)

    # pytest crashed before producing a report (e.g. no tests collected, import error)
    if not json_report_path.exists():
        return {
            "results": {
                "passed": 0,
                "failed": 0,
                "total": 0,
                "stdout": proc.stdout + proc.stderr,
                "returncode": proc.returncode,
            },
            "failures": [
                {
                    "test_name": "collection_error",
                    "failure_type": "test_bug",
                    "message": proc.stdout + proc.stderr,
                    "longrepr": proc.stdout + proc.stderr,
                    "file_path": "",
                }
            ],
        }

    report = json.loads(json_report_path.read_text(encoding="utf-8"))
    summary = report.get("summary", {})

    all_tests = []
    failures = []

    for test in report.get("tests", []):
        outcome = test["outcome"]
        call = test.get("call", {})
        setup = test.get("setup", {})
        # Strip the directory prefix to get a readable name: test_posts.py::test_get_post_happy_path
        short_name = "::".join(test["nodeid"].split("::")[-2:])

        all_tests.append({
            "name": short_name,
            "outcome": outcome,
            "duration": round(test.get("call", {}).get("duration", 0), 3),
        })

        if outcome in ("failed", "error"):
            failures.append({
                "test_name": test["nodeid"],
                "failure_type": None,
                "message": call.get("longrepr") or setup.get("longrepr", ""),
                "longrepr": call.get("longrepr") or setup.get("longrepr", ""),
                "file_path": test["nodeid"].split("::")[0],
            })

    print(f"\n  pytest: {summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed"
          f" — retry {state['retry_count']}")

    return {
        "results": {
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "total": summary.get("total", 0),
            "tests": all_tests,
            "stdout": proc.stdout,
            "returncode": proc.returncode,
        },
        "failures": failures,
    }
