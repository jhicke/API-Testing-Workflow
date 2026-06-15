import json
from typing import Literal

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import BASE_API_URL, MAX_TOKENS, MODEL_NAME, REPORTS_DIR, TESTPLAN_DIR
from graph.state import QAState

PLAN_CACHE_FILE = TESTPLAN_DIR / ".cache.json"
PLAN_FILE = TESTPLAN_DIR / "test_plan.json"


def _load_plan_cache() -> dict:
    if PLAN_CACHE_FILE.exists():
        return json.loads(PLAN_CACHE_FILE.read_text(encoding="utf-8"))
    return {}


class PlanCase(BaseModel):
    endpoint_path: str
    method: str
    scenario: Literal["happy_path", "not_found", "invalid_input", "edge_case"]
    description: str
    expected_status: int
    test_data: dict


class Plan(BaseModel):
    cases: list[PlanCase]


def _write_plan_to_run_dir(plan: list, run_id: str) -> None:
    run_dir = REPORTS_DIR / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "test_plan.json").write_text(
        json.dumps(plan, indent=2), encoding="utf-8"
    )


def planner(state: QAState) -> dict:
    if state.get("error"):
        return {}

    spec_hash = state.get("spec_hash", "")

    # Cache hit — reuse existing test plan if spec hasn't changed
    if spec_hash:
        cache = _load_plan_cache()
        if spec_hash in cache and PLAN_FILE.exists():
            plan = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
            print(f"  (plan cache hit — reusing existing test plan in {TESTPLAN_DIR})")
            _write_plan_to_run_dir(plan, state["run_id"])
            return {"plan": plan}

    llm = ChatAnthropic(model=MODEL_NAME, temperature=0, max_tokens=MAX_TOKENS)
    structured_llm = llm.with_structured_output(Plan)

    spec = state["spec"]
    endpoints_json = json.dumps(
        [
            {
                "path": e["path"],
                "method": e["method"],
                "summary": e["summary"],
                "parameters": e["parameters"],
                "requestBody": e["requestBody"],
                "responses": e["responses"],
            }
            for e in spec["endpoints"]
        ],
        indent=2,
    )

    prompt = f"""You are a QA engineer creating a minimal test plan for a REST API.

API: {spec['title']}
Base URL: {BASE_API_URL}

Endpoints:
{endpoints_json}

Generate at most 5 test cases total. Only include scenarios that apply:
- GET list → happy_path only
- GET by ID → happy_path + not_found
- POST/PUT/PATCH → happy_path with realistic test_data
- DELETE → happy_path + not_found

Rules:
- expected_status must match what the spec says the API actually returns
- test_data should be a dict of values to send (empty dict if none needed)
- Each endpoint includes a "testIds" field. If present, use testIds.valid for happy_path and testIds.invalid for not_found. If absent, fall back to ID 1 for valid and 99999 for invalid.
"""

    try:
        result = structured_llm.invoke(prompt)
        plan = [case.model_dump() for case in result.cases]

        # Save to cache
        TESTPLAN_DIR.mkdir(parents=True, exist_ok=True)
        PLAN_FILE.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        if spec_hash:
            cache = _load_plan_cache()
            cache[spec_hash] = state["run_id"]
            PLAN_CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

        _write_plan_to_run_dir(plan, state["run_id"])
        return {"plan": plan}
    except Exception as e:
        return {"error": f"planner failed: {e}"}
