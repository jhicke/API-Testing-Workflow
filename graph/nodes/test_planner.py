import json
from typing import Literal

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import BASE_API_URL, MODEL_NAME, REPORTS_DIR, TESTPLAN_DIR
from graph.state import QAState

PLAN_CACHE_FILE = TESTPLAN_DIR / ".cache.json"
PLAN_FILE = TESTPLAN_DIR / "test_plan.json"


def _load_plan_cache() -> dict:
    if PLAN_CACHE_FILE.exists():
        return json.loads(PLAN_CACHE_FILE.read_text(encoding="utf-8"))
    return {}


class TestCase(BaseModel):
    endpoint_path: str
    method: str
    scenario: Literal["happy_path", "not_found", "invalid_input", "edge_case"]
    description: str
    expected_status: int
    test_data: dict


class TestPlan(BaseModel):
    cases: list[TestCase]


def _write_plan_to_run_dir(plan: list, run_id: str) -> None:
    run_dir = REPORTS_DIR / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "test_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")


def test_planner(state: QAState) -> dict:
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

    llm = ChatAnthropic(model=MODEL_NAME, temperature=0)
    structured_llm = llm.with_structured_output(TestPlan)

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

    prompt = f"""You are a QA engineer creating a test plan for a REST API.

API: {spec['title']}
Base URL: {BASE_API_URL}

Endpoints:
{endpoints_json}

Create a comprehensive test plan. For each endpoint generate test cases covering:
1. happy_path — valid inputs, expected success response
2. not_found — request a non-existent resource (use ID 99999), expect 404
3. invalid_input — missing required fields or wrong types, expect 4xx
4. edge_case — boundary values, empty query params, filtering

Rules:
- Not every endpoint needs every scenario — use judgement
- POST/PUT/PATCH must have a happy_path with realistic test_data
- DELETE must have happy_path and not_found
- expected_status must match what the spec says the API actually returns
- test_data should be a dict of values to send (empty dict if none needed)
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
        return {"error": f"test_planner failed: {e}"}
