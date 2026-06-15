import json
from datetime import datetime
from pathlib import Path
from statistics import mean

import pytest

from config import REPORTS_DIR
from evaluation.evals.judge import Score, judge
from evaluation.evals.rubrics import FAILURE_ANALYZER_RUBRIC, FIX_SUGGESTER_RUBRIC, PLANNER_RUBRIC

DATASETS = Path(__file__).parent / "datasets"
JUDGE_RUNS = 3
PASS_THRESHOLD = 4.0

# Accumulated results written to a report at the end of the eval run
_eval_results: list[dict] = []


def _load(filename: str) -> list:
    return json.loads((DATASETS / filename).read_text(encoding="utf-8"))


def _score_fixture(rubric: str, node_input: dict, node_output: dict) -> tuple[float, list[Score]]:
    input_str = json.dumps(node_input, indent=2)
    output_str = json.dumps(node_output, indent=2)
    scores = [judge(rubric, input_str, output_str) for _ in range(JUDGE_RUNS)]
    return mean(s.score for s in scores), scores


def _run_eval(node_name: str, rubric: str, dataset_file: str) -> None:
    node_results = []
    for i, fixture in enumerate(_load(dataset_file), start=1):
        mean_score, scores = _score_fixture(rubric, fixture["input"], fixture["output"])
        node_results.append({
            "fixture": i,
            "mean_score": mean_score,
            "scores": [{"score": s.score, "reasoning": s.reasoning} for s in scores],
            "expected": fixture["expected"],
            "passed": mean_score >= PASS_THRESHOLD,
        })
        assert mean_score >= PASS_THRESHOLD, (
            f"{node_name} eval failed (mean={mean_score:.1f}). Expected: {fixture['expected']}"
        )
    _eval_results.append({"node": node_name, "fixtures": node_results})


def _write_eval_report() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"eval_{timestamp}.md"

    lines = [f"# Eval Report — {timestamp}", ""]
    lines += [
        f"**Judge model:** claude-haiku-4-5-20251001  ",
        f"**Judge runs per fixture:** {JUDGE_RUNS}  ",
        f"**Pass threshold:** {PASS_THRESHOLD}",
        "",
    ]

    summary_rows = []
    for result in _eval_results:
        all_passed = all(f["passed"] for f in result["fixtures"])
        mean_all = mean(f["mean_score"] for f in result["fixtures"])
        status = "✅ PASS" if all_passed else "❌ FAIL"
        summary_rows.append((result["node"], f"{mean_all:.1f}", status))

    lines += ["## Summary", ""]
    lines += ["| Node | Mean Score | Status |", "|------|-----------|--------|"]
    for node, score, status in summary_rows:
        lines.append(f"| {node} | {score} | {status} |")
    lines.append("")

    for result in _eval_results:
        lines += [f"## {result['node']}", ""]
        for f in result["fixtures"]:
            status = "✅ PASS" if f["passed"] else "❌ FAIL"
            lines += [
                f"### Fixture {f['fixture']} — {status} (mean={f['mean_score']:.1f})",
                "",
                f"**Expected:** {f['expected']}",
                "",
                "**Judge runs:**",
                "",
            ]
            for j, s in enumerate(f["scores"], start=1):
                lines += [
                    f"- Run {j} — score {s['score']}: {s['reasoning']}",
                ]
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEval report written to {report_path}")


@pytest.mark.eval
class TestPlannerEval:
    def test_planner_coverage(self):
        _run_eval("Planner", PLANNER_RUBRIC, "planner.json")


@pytest.mark.eval
class TestFailureAnalyzerEval:
    def test_failure_analyzer_correctness(self):
        _run_eval("Failure Analyzer", FAILURE_ANALYZER_RUBRIC, "failure_analyzer.json")


@pytest.mark.eval
class TestFixSuggesterEval:
    def test_fix_quality(self):
        _run_eval("Fix Suggester", FIX_SUGGESTER_RUBRIC, "fix_suggester.json")
        _write_eval_report()
