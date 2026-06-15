from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class QAState(TypedDict):
    spec: dict  # Parsed OpenAPI spec (starts as {"path": "..."}, becomes full spec)
    plan: list  # Structured test plan from planner
    tests: list  # File paths of generated test files
    results: dict  # pytest summary (passed, failed, total)
    failures: list  # Per-failure details, classified by failure_analyzer
    fixes: list  # Log of fixes applied by fix_suggester
    messages: Annotated[list, add_messages]  # Full LLM message history
    retry_count: int  # How many self-healing retries have been attempted
    run_id: str  # Timestamp string — ties together test dir and report dir
    spec_hash: str  # SHA-256 of spec file content — used for test caching
    error: str  # Set by any node that fails gracefully
