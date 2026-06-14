import json
from datetime import datetime
from pathlib import Path

from config import REPORTS_DIR
from graph.state import QAState


def report_writer(state: QAState) -> dict:
    run_dir = REPORTS_DIR / f"run_{state['run_id']}"
    run_dir.mkdir(parents=True, exist_ok=True)

    results = state.get("results", {})
    failures = state.get("failures", [])
    fixes = state.get("fixes", [])
    error = state.get("error", "")

    passed = results.get("passed", 0)
    failed = results.get("failed", 0)
    total = results.get("total", 0)

    if error:
        status = "ERROR"
    elif failed == 0 and total > 0:
        status = "PASS"
    elif passed > 0:
        status = "PARTIAL"
    else:
        status = "FAIL"

    # ── JSON report ──────────────────────────────────────────────────────────

    all_tests = results.get("tests", [])

    report_data = {
        "run_id": state["run_id"],
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "spec_title": state.get("spec", {}).get("title", "Unknown"),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "retries": state["retry_count"],
        },
        "tests": all_tests,
        "fixes_applied": fixes,
        "remaining_failures": [
            {
                "test": f["test_name"],
                "type": f.get("failure_type", "unknown"),
                "reason": f.get("reason", ""),
                "message": f.get("message", "")[:500],
            }
            for f in failures
        ],
        "error": error,
    }

    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    # ── Markdown report ───────────────────────────────────────────────────────

    lines = [
        f"# QA Report — {state['run_id']}",
        f"",
        f"**Status:** {status}",
        f"**API:** {report_data['spec_title']}",
        f"**Timestamp:** {report_data['timestamp']}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total tests | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Self-healing retries | {state['retry_count']} |",
        f"",
    ]

    if all_tests:
        lines += ["## Test Results", ""]
        lines.append("| Test | Result | Duration |")
        lines.append("|------|--------|----------|")
        for t in all_tests:
            icon = "✅" if t["outcome"] == "passed" else "❌"
            lines.append(f"| `{t['name']}` | {icon} {t['outcome']} | {t['duration']}s |")
        lines.append("")

    if fixes:
        lines += ["## Fixes Applied", ""]
        for fix in fixes:
            lines.append(f"- **Retry {fix['retry']}** — `{fix['filename']}`: {fix['changes']}")
        lines.append("")

    if failures:
        lines += ["## Remaining Failures", ""]
        for f in failures:
            lines.append(f"### `{f['test_name']}`")
            lines.append(f"- **Type:** {f.get('failure_type', 'unknown')}")
            lines.append(f"- **Reason:** {f.get('reason', 'N/A')}")
            if f.get("message"):
                lines.append(f"- **Details:** `{f['message'][:300]}`")
            lines.append("")

    if error:
        lines += ["## Error", "", "```", error, "```", ""]

    md_path = run_dir / "report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # ── Console summary ───────────────────────────────────────────────────────

    print(f"\n{'='*55}")
    print(f"  Status : {status}")
    print(f"  Tests  : {passed}/{total} passed")
    print(f"  Retries: {state['retry_count']}")
    print(f"  Reports: {run_dir}")
    print(f"{'='*55}\n")

    return {}
