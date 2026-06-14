# AI Test Engineer

An autonomous QA agent built with LangGraph and Claude. It ingests an OpenAPI spec, generates pytest test files, runs them, self-heals failures, and produces a report.

---

## Prerequisites

- Python 3.11+
- An Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
# Copy .env.example to .env and fill in your key
copy .env.example .env
# Then open .env and replace the placeholder with your real key
```

---

## Running

```bash
# Full run — parse spec, generate tests, run them, self-heal, write report
python app.py jsonplaceholder_spec.yaml

# Skip test generation — force reuse of existing tests regardless of spec changes
# Use this to test self-healing, NOT after changing the spec
python app.py jsonplaceholder_spec.yaml --reuse-tests

# Pause before running tests so you can inspect the generated files first
python app.py jsonplaceholder_spec.yaml --review
```

---

## Output

Each run produces a timestamped report directory:

```
reports/run_<timestamp>/
    report.md     # human-readable summary with per-test results table
    report.json   # structured output for CI / dashboards
```

Generated test files live in `generated/`. On every run, the spec file is hashed — if the hash matches the previous run, test generation is skipped entirely and the existing files are reused. If the spec changed, new tests are generated and the old files are overwritten.

---

## How it works

```
spec_parser    reads and parses the OpenAPI spec file
    → planner      asks Claude to create a structured test plan
    → generator    asks Claude to write pytest files from the plan
    → runner       runs pytest as a subprocess, captures results
        → (failures)  failure_analyzer  classifies each failure:
                                        test_bug / spec_bug / backend_bug
                      fix_suggester     rewrites failing test files (test_bugs only)
                      runner            re-runs — up to 3 retries
        → (passing)   report_writer     writes report.md and report.json
```

The self-healing loop retries up to `MAX_RETRIES` times (default 3). Only `test_bug` failures are auto-fixed — `spec_bug` and `backend_bug` are reported as findings.

Graph 
 spec_parser ──→ planner ──→ generator ──→ runner
                                                         │
                                                    any failures?
                                                    ┌────┴─────┐
                                                   yes        no
                                                    ↓          ↓
                                           failure_analyzer  report_writer
                                                    ↓
                                            fix_suggester
                                                    ↓
                                            test_runner  (loop, up to 3x)

---

## Testing a different API

Swap in any OpenAPI 3.0 spec (JSON or YAML):

```bash
python app.py path/to/your-api-spec.yaml
```

---

## Project structure

```
app.py                      CLI entrypoint
config.py                   All tuneable values (model, retries, paths)
jsonplaceholder_spec.yaml   Example OpenAPI spec for JSONPlaceholder

graph/
    state.py                QAState TypedDict — shared state across all nodes
    graph_builder.py        LangGraph wiring — nodes, edges, routing functions
    nodes/
        spec_parser.py      Parse OpenAPI spec, resolve $ref pointers, check cache
        planner.py          Claude generates structured test plan
        generator.py        Claude writes pytest files from the plan
        runner.py           Runs pytest subprocess, parses JSON report
        failure_analyzer.py Claude classifies each failure
        fix_suggester.py    Claude rewrites broken test files
        report_writer.py    Writes report.md and report.json

generated/                  Generated test files (gitignored)
reports/                    Run reports (gitignored)
```

---

## Key design decisions

| Decision | Reason |
|---|---|
| LangGraph over plain Python | Built-in state management, conditional routing, and retry loops |
| `with_structured_output()` | Claude returns typed Pydantic objects, not strings to parse |
| `pytest-json-report` | Structured failure data instead of scraping stdout |
| Spec hash caching | Skip regeneration when the spec hasn't changed |
| Only fix `test_bug` failures | Auto-fixing `spec_bug`/`backend_bug` would mask real defects |
| `temperature=0` on all LLM calls | Deterministic output — same spec produces consistent tests |
