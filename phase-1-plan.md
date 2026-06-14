# AI Test Engineer — Project Handover

## Project Overview

Build a LangGraph-based multi-agent system that acts as an autonomous QA engineer. It ingests an OpenAPI spec, generates and runs tests, analyzes failures, applies fixes automatically, and produces a final report.

---

## Architecture Decisions (Agreed in Planning)

### LLM Backend: LangChain ChatAnthropic
Use `langchain_anthropic.ChatAnthropic` rather than the Anthropic SDK directly. Rationale:
- Native LangGraph integration (same ecosystem)
- `.with_structured_output()` handles structured node responses cleanly
- Built-in retry and rate limit handling
- Easy model swapping if needed

### Practice API: JSONPlaceholder
- Base URL: `https://jsonplaceholder.typicode.com`
- No auth required, always live
- Endpoints: `/posts`, `/users`, `/comments`, `/todos`
- Covers GET, POST, PUT, PATCH, DELETE
- Predictable responses — good for meaningful pass/fail testing

### Self-Healing Loop: Ambitious Version
The fix suggester should **automatically apply fixes** to generated test files and re-run — not just suggest them. Cap retries at 3 to avoid infinite loops.

### Test Runner Isolation
Each run gets a timestamped directory: `tests/generated/run_<timestamp>/`. pytest runs as a subprocess pointed at that directory. Keeps history, no working directory pollution.

### Report Format: Both
- `report.md` — human-readable summary
- `report.json` — structured output for future tooling (CI, dashboards)
- Both land in `reports/run_<timestamp>/`

---

## Graph Flow

```
spec_parser
    → test_planner
    → test_generator
    → test_runner
        → (failures AND retry_count < MAX_RETRIES) failure_analyzer → fix_suggester → test_runner
        → (failures AND retry_count >= MAX_RETRIES) report_writer → END   # give up, report what failed
        → (no failures)                              report_writer → END
```

The conditional edge out of `test_runner` is a single routing function that returns one of
three targets based on `results` and `retry_count`:

```python
def route_after_run(state: QAState) -> str:
    if not state["failures"]:
        return "report_writer"          # all green
    if state["retry_count"] >= MAX_RETRIES:
        return "report_writer"          # exhausted retries — report remaining failures
    return "failure_analyzer"           # try to self-heal

# fix_suggester is responsible for incrementing retry_count before handing back to test_runner
```

> The report must clearly distinguish *passed*, *fixed-then-passed*, and *still-failing-after-N-retries*
> so an exhausted loop doesn't look like a clean run.

---

## Node Breakdown

| Node | Responsibility |
|---|---|
| `spec_parser` | Ingest and parse OpenAPI spec into structured endpoints/schemas |
| `test_planner` | Generate a structured test plan (what to test and why) |
| `test_generator` | Produce executable pytest files from the plan |
| `test_runner` | Run pytest in a subprocess, capture results |
| `failure_analyzer` | Classify failures (test bug vs spec bug vs backend bug) |
| `fix_suggester` | Generate and **apply** fixes to test files automatically |
| `report_writer` | Write `report.md` and `report.json` |

---

## Shared State Schema

```python
class QAState(TypedDict):
    spec: dict               # Parsed OpenAPI spec
    plan: list               # Structured test plan
    tests: list              # Generated test file paths
    results: dict            # pytest output
    failures: list           # Parsed failure details
    fixes: list              # Applied fixes log
    messages: Annotated[list, add_messages]  # LLM message history (for debugging) — reducer so nodes append, not overwrite
    retry_count: int         # Self-healing loop counter (max 3)
    run_id: str              # Timestamp-based run identifier
```

> **Note:** `retry_count` and `run_id` were added beyond the original handover doc. Both are required for the self-healing loop and run isolation.

---

## File Structure

```
ai-test-engineer/
│
├── app.py                        # CLI entrypoint
├── config.py                     # Model name, paths, retry limit, API key source
├── requirements.txt
├── .gitignore
│
├── graph/
│   ├── state.py                  # QAState TypedDict
│   ├── graph_builder.py          # LangGraph builder + edges
│   └── nodes/
│       ├── spec_parser.py
│       ├── test_planner.py
│       ├── test_generator.py
│       ├── test_runner.py
│       ├── failure_analyzer.py
│       ├── fix_suggester.py
│       └── report_writer.py
│
├── tests/
│   └── generated/                # gitignored — timestamped run dirs live here
│
└── reports/                      # gitignored — timestamped report dirs live here
```

---

## Config Layer (`config.py`)

Centralise all tuneable values here so nothing is hardcoded in node files:

```python
MODEL_NAME = "claude-sonnet-4-6"
MAX_RETRIES = 3
GENERATED_TESTS_DIR = Path("tests/generated")
REPORTS_DIR = Path("reports")
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
BASE_API_URL = "https://jsonplaceholder.typicode.com"
```

---

## Design Principles

- **Deterministic flow** — LangGraph handles all routing; no surprise branching
- **Clear state transitions** — every node reads from and writes to `QAState` only
- **Minimal dependencies** — `langgraph`, `langchain-anthropic`, `pytest`, `pytest-json-report`, `requests` (`pathlib` is stdlib, not a dependency)
- **Easy to debug** — `messages` field in state captures full LLM history
- **Easy to extend** — each node is an isolated Python file
- **Claude handles reasoning; Python handles execution**

---

## Key Implementation Notes

1. Use `pathlib.Path` throughout — no raw string paths
2. Support a `--review` CLI flag that compiles the graph with `interrupt_before=["test_runner"]` so generated tests can be inspected before execution. Note: `interrupt_before` requires the graph to be compiled with a checkpointer (e.g. `MemorySaver`) and the run to use a `thread_id`, otherwise the interrupt is silently ignored. Default (no flag) runs straight through.
3. `fix_suggester` should write changes directly to the test files in the run directory, then hand back to `test_runner`
4. `failure_analyzer` classifies each failure into one of: `test_bug`, `spec_bug`, `backend_bug` — this classification drives what `fix_suggester` does. Only `test_bug` failures are safely auto-fixable; `spec_bug` and `backend_bug` should be reported, not "fixed" by editing the test to pass (otherwise the loop just masks real defects)
5. `tests/generated/` and `reports/` should both be in `.gitignore`
6. `test_runner` should run pytest with `--json-report` (the `pytest-json-report` plugin) and parse the resulting JSON file rather than scraping stdout. Populate `results` from the summary and `failures` from the per-test failure entries — robust parsing is what makes the self-healing loop trustworthy
7. Distinguish *test failures* (assertions) from *collection/execution errors* (import errors, syntax errors in generated files). A generated file that won't even import is a `test_bug` the fixer must handle, not a backend signal
8. Each node should fail gracefully — a malformed spec or an LLM call that returns unparseable output should route to `report_writer` with a clear error rather than crashing the graph

---

## Deliverables Expected from Claude Code

1. All Python files with full working code (not skeletons)
2. LLM prompts for each AI-powered node
3. `requirements.txt` and `.gitignore`
4. CLI usage instructions
5. Sample run output using JSONPlaceholder spec
6. Ideas for future extensions

---

## Future Extension Ideas

- Web UI (Streamlit or FastAPI) to upload specs and view reports
- Support for authenticated APIs (Bearer token, OAuth)
- Parallel test generation per endpoint
- GitHub Actions integration for CI usage
- Vector store memory so the agent learns from past runs
- Support for GraphQL specs
