import json
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import BASE_API_URL, GENERATED_TESTS_DIR, MAX_TOKENS, MODEL_NAME
from graph.nodes.spec_parser import CACHE_FILE, _load_cache
from graph.state import QAState


class GeneratedTestFile(BaseModel):
    filename: str
    content: str


class GeneratedTests(BaseModel):
    files: list[GeneratedTestFile]


def generator(state: QAState) -> dict:
    if state.get("error"):
        return {}

    llm = ChatAnthropic(model=MODEL_NAME, temperature=0, max_tokens=MAX_TOKENS)
    structured_llm = llm.with_structured_output(GeneratedTests)

    plan_json = json.dumps(state["plan"], indent=2)

    prompt = f"""You are a pytest expert. Generate executable pytest test files from this test plan.

Base URL: {BASE_API_URL}

Test Plan:
{plan_json}

Rules:
- Use the `requests` library for all HTTP calls
- Each test function must be completely standalone — no shared fixtures or conftest.py
- Function names: test_<method>_<resource>_<scenario>  e.g. test_get_post_happy_path
- Always assert BOTH the status code AND at least one field in the response body
- For 404 tests use the invalid ID from the test plan's test_data (e.g. the id field); if not specified fall back to 99999
- Only import: requests, pytest (no other third-party libraries)
- Group tests by resource tag into one file per resource (posts, users, todos, comments)
- Filename format: test_<resource>.py
- Never use pytest.mark.xfail, pytest.mark.skip, or pytest.mark.skipif — every test must assert a definitive expected status code
- A 500 response in the spec means assert response.status_code == 500, not an xfail marker
"""

    try:
        result = structured_llm.invoke(prompt)
    except Exception as e:
        return {"error": f"test_generator failed: {e}"}

    GENERATED_TESTS_DIR.mkdir(parents=True, exist_ok=True)
    (GENERATED_TESTS_DIR / "__init__.py").write_text("")

    written_paths = []
    for tf in result.files:
        file_path = GENERATED_TESTS_DIR / tf.filename
        file_path.write_text(tf.content, encoding="utf-8")
        written_paths.append(str(file_path))

    # Save to cache so future runs with the same spec skip generation
    if state.get("spec_hash"):
        cache = _load_cache()
        cache[state["spec_hash"]] = state["run_id"]
        CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    return {"tests": written_paths}
