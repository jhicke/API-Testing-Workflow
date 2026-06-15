# AI API Testing Workflow

An autonomous QA agent that reads an OpenAPI spec and, without human input, plans a test suite, writes pytest files, runs them, classifies failures, self-heals what it can, and writes a structured report. Built with LangGraph and Claude.

A companion eval suite verifies the agent's own output quality using unit tests and an LLM-as-judge approach.

---

## How it works

```
spec_parser → planner → generator → runner
                                        │
                                   any failures?
                                  ┌─────┴──────┐
                                 yes            no
                                  ↓              ↓
                         failure_analyzer    report_writer
                                  ↓
                           fix_suggester
                                  ↓
                            runner  (loop, up to 3x)
                                  ↓
                            report_writer
```

Each node is a function that reads shared state and returns only what it changed. LangGraph handles merging and routing.

| Node | Type | What it does |
|---|---|---|
| `spec_parser` | Python | Parses YAML/JSON spec, resolves `$ref` pointers, checks cache |
| `planner` | LLM | Claude generates a structured test plan (Pydantic-enforced) |
| `generator` | LLM | Claude writes pytest files from the plan |
| `runner` | Python | Runs pytest as a subprocess, parses JSON results |
| `failure_analyzer` | LLM | Classifies each failure: `test_bug`, `spec_bug`, or `backend_bug` |
| `fix_suggester` | LLM | Rewrites test files for `test_bug` failures only |
| `report_writer` | Python | Writes `report.md` and `report.json` per run |

Only `test_bug` failures are auto-fixed. `spec_bug` and `backend_bug` are surfaced in the report — auto-fixing those would hide real defects.

---

## Prerequisites

- Python 3.11+
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com)
- LangSmith API key (optional, for tracing) — [smith.langchain.com](https://smith.langchain.com)

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Open .env and fill in your API keys
```

---

## Running the agent

```bash
# Full run — parse spec, plan, generate, run, self-heal, report
python app.py jsonplaceholder_spec.yaml

# Force reuse of existing generated tests (for testing self-healing only)
python app.py jsonplaceholder_spec.yaml --reuse-tests

# Pause before running tests so you can inspect the generated files first
python app.py jsonplaceholder_spec.yaml --review

# Clear cache and generated files to force a clean run
python clear_cache.py
```

Each run writes a timestamped report:

```
reports/run_<timestamp>/
    report.md     human-readable summary with per-test results table
    report.json   structured output for CI / dashboards
    test_plan.json  the plan Claude generated for this run
```

Generated test files live in `generated/`. The spec is SHA-256 hashed on every run — if the hash matches the previous run, test planning and generation are skipped entirely. If the spec changed, everything regenerates.

---

## Testing a different API

Swap in any OpenAPI 3.0 spec (JSON or YAML):

```bash
python app.py path/to/your-api-spec.yaml
```

---

## Eval suite

The `evaluation/` directory tests the agent itself across two layers.

**Layer 1 — Unit tests** (fast, no LLM calls, runs on every `pytest`):
- Routing logic: does `route_after_parse` go to the right node in every case?
- State reducers: does `add_messages` append correctly? Does `retry_count` stop the loop?
- Node behavior: do nodes short-circuit on error? Do they call the LLM exactly once?

**Layer 3 — LLM-as-judge evals** (slow, makes real LLM calls, run on demand):
- Claude Haiku scores each AI node's output against a prose rubric
- Each fixture is judged 3 times and scores are averaged to reduce noise
- Pass threshold: mean score ≥ 4.0 out of 5
- Datasets harvested from real LangSmith traces

```bash
# Run unit tests only (default)
pytest

# Run LLM-as-judge evals
pytest -m eval
```

Eval results are written to `reports/eval_<timestamp>.md` with a summary table and per-fixture judge reasoning.

---

## Observability

LangSmith tracing is enabled via `.env`. Every LLM call in the graph is automatically traced — prompts, responses, latency, token counts — without any changes to agent code. Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` in `.env`.

---

## Project structure

```
app.py                          CLI entrypoint
config.py                       All tuneable values (model, retries, paths)
clear_cache.py                  Deletes generated files and plan cache
jsonplaceholder_spec.yaml       Example OpenAPI spec

graph/
    state.py                    QAState TypedDict — shared state across all nodes
    graph_builder.py            LangGraph wiring — nodes, edges, routing functions
    nodes/
        spec_parser.py
        planner.py
        generator.py
        runner.py
        failure_analyzer.py
        fix_suggester.py
        report_writer.py

evaluation/
    conftest.py                 Shared pytest fixtures (sample_state)
    unit/
        test_routing.py         Tests for route_after_parse and route_after_run
        test_nodes.py           Tests for each LLM node with mocked ChatAnthropic
        test_state.py           Tests for state reducers and retry boundary
    evals/
        judge.py                LLM-as-judge harness using Claude Haiku
        rubrics.py              Scoring rubrics for planner, failure_analyzer, fix_suggester
        test_evals.py           pytest -m eval entry point
        datasets/
            planner.json
            failure_analyzer.json
            fix_suggester.json

generated/                      Generated test files (gitignored)
reports/                        Run and eval reports (gitignored)
testplan/                       Plan cache (gitignored)
```

---

## Key design decisions

| Decision | Reason |
|---|---|
| LangGraph over plain Python | Built-in state management, conditional routing, and retry loops without custom orchestration code |
| `with_structured_output()` | Claude returns typed Pydantic objects — no string parsing, schema violations raise immediately |
| `pytest-json-report` | Structured failure data instead of scraping stdout |
| Spec hash caching | Skip LLM calls entirely when the spec hasn't changed |
| Only fix `test_bug` failures | Auto-fixing `spec_bug` or `backend_bug` would mask real defects in the report |
| `temperature=0` on all LLM calls | Deterministic output — same spec produces consistent tests across runs |
| Haiku for eval judge | Cheaper and faster for scoring tasks; no need for the full capability of the production model |
| pytest markers for evals | Prevents costly LLM-as-judge tests from running in the normal fast-feedback loop |
