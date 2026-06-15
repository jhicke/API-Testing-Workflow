import pytest


@pytest.fixture
def sample_state(tmp_path):
    """Minimal valid QAState for driving nodes and routers in tests."""
    return {
        "spec": {"title": "Test API", "endpoints": []},
        "plan": [],
        "tests": [],
        "results": {},
        "failures": [],
        "fixes": [],
        "messages": [],
        "retry_count": 0,
        "run_id": "test_run",
        "spec_hash": "",
        "error": "",
    }
