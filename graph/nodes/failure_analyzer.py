import json
from pathlib import Path
from typing import Literal

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import MODEL_NAME
from graph.state import QAState


class FailureAnalysis(BaseModel):
    test_name: str
    failure_type: Literal["test_bug", "spec_bug", "backend_bug"]
    reason: str
    suggested_fix: str


class FailureReport(BaseModel):
    analyses: list[FailureAnalysis]


def failure_analyzer(state: QAState) -> dict:
    if state.get("error") or not state.get("failures"):
        return {}

    llm = ChatAnthropic(model=MODEL_NAME, temperature=0)
    structured_llm = llm.with_structured_output(FailureReport)

    # Read current test file contents so Claude can see the actual code
    test_files = {}
    for test_path in state.get("tests", []):
        p = Path(test_path)
        if p.exists():
            test_files[p.name] = p.read_text(encoding="utf-8")

    failures_json = json.dumps(state["failures"], indent=2)
    files_json = json.dumps(test_files, indent=2)

    prompt = f"""You are a QA analyst. Classify each pytest failure into exactly one category.

Categories:
- test_bug: The test code itself is wrong — bad URL, wrong expected status code, wrong assertion,
  missing field, syntax error, or wrong test data. The API is fine; the test is the problem.
- spec_bug: The test logic is correct but the OpenAPI spec described the API inaccurately.
  The test did what the spec said, but the real API behaves differently.
- backend_bug: The API is genuinely broken. The test is correct, the spec is correct,
  but the API returned something wrong.

Important guidance:
- Most failures in a generated test suite are test_bugs — Claude writes tests based on a spec
  and sometimes gets details wrong
- Only classify as backend_bug if the API clearly violated its own documented contract
- For test_bug, suggested_fix must be specific: name the exact line or value to change
- For spec_bug and backend_bug, suggested_fix should explain what the discrepancy is

Failures:
{failures_json}

Test file contents:
{files_json}
"""

    try:
        result = structured_llm.invoke(prompt)
    except Exception as e:
        return {"error": f"failure_analyzer failed: {e}"}

    analysis_map = {a.test_name: a for a in result.analyses}

    updated_failures = []
    for failure in state["failures"]:
        analysis = analysis_map.get(failure["test_name"])
        if analysis:
            updated_failures.append({
                **failure,
                "failure_type": analysis.failure_type,
                "reason": analysis.reason,
                "suggested_fix": analysis.suggested_fix,
            })
        else:
            updated_failures.append(failure)

    return {"failures": updated_failures}
