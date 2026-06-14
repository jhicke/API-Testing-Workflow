# Phase 2 Plan — Evals & Observability

## Goal

Learn how to test AI and agent-based systems by building an eval suite for the existing QA agent. This phase treats the agent itself as the system under test.

---

## What We're Learning

Phase 1 taught LangGraph, structured LLM output, and agentic loops. Phase 2 teaches:

- **How AI teams catch regressions** — evals, not just unit tests
- **How to debug multi-step agents** — LangSmith tracing
- **LLM-as-judge** — using Claude to score Claude's outputs
- **The evals mindset** — asserting on quality, not exact string equality

These are the questions this phase lets you answer in an interview:
> "How do you know your LLM outputs are good?"
> "How do you catch regressions when you change a prompt?"
> "How do you debug an agent that fails mid-graph?"

---

## Why Not Build a New Agent First?

The suggestion to build a CRUD agent against JSONPlaceholder and test that was considered. Decision: skip it. You already have a non-trivial agent with real AI decisions — test planner, failure classifier, fix suggester. That's a more interesting and realistic subject than a throwaway API client.

---

## Three Layers of AI Testing

### Layer 1 — Deterministic Node Tests
Standard pytest, LLM calls mocked with fixed responses. Tests structural correctness and graph routing, not LLM quality.

What to cover:
- Each node returns the expected state keys
- `route_after_run` routes correctly for all four cases: `error` short-circuit, all-pass, fixable failure, exhausted retries
- `route_after_parse` routes correctly: `error` → report, cache hit → runner, otherwise → planner
- Retry counter caps at `MAX_RETRIES`
- Malformed spec sets `error` and routes to `report_writer` gracefully rather than crashing

### Layer 2 — LangSmith Tracing
Wire LangSmith into the existing graph. Every run produces a trace showing each node, its inputs/outputs, latency, and token usage. This is the foundation for everything else — you can't write evals against outputs you can't inspect.

What you get:
- Full visibility into every LLM call
- A UI to browse runs and compare them
- The input/output pairs needed to build evals

### Layer 3 — LLM-as-Judge Evals
Use Claude to score the quality of outputs from the AI nodes. Assert that scores meet a threshold.

Examples:
- **Test planner eval:** Does the generated test plan cover the endpoints described in the spec? Score 1–5.
- **Failure classifier eval:** Given a failure message and classification, was the classification correct? Yes/No with reasoning.
- **Fix suggester eval:** Does the suggested fix actually address the failure described? Score 1–5.

Each eval is a Python function that calls Claude with a rubric and returns a score. Run them as part of the test suite against real LLM output (no mocking).

---

## Success Criteria & Eval Dataset

The evals need acceptance criteria, or a red suite just gets ignored.

### Pass bars
- **Score evals (planner, fixer):** 1–5 scale, pass at **mean ≥ 4**.
- **Yes/No evals (classifier):** **100% correct** on the dataset.

### Sampling (handling judge noise)
- LLM-as-judge scores wobble ±1 run-to-run. Run each eval **3× per example** and take the mean; the suite fails only if the mean drops below the bar — not a single bad sample.

### Eval dataset
- Commit **3–5 fixtures per node** under `evaluation/evals/datasets/` (JSON/YAML, version-controlled so changes show in diffs).
- Each fixture = input (spec fragment / failure message) + a loose "expected" note for the judge's rubric.
- **Harvest fixtures from real runs once LangSmith is wired** — tracing gives the input/output pairs for free. This means dataset work comes *after* tracing, not before.

### Test suite gating (speed & determinism, not cost)
- **Layer 1 (mocked node tests)** run in the default `pytest` on every commit — fast and deterministic, so a red test means a real regression.
- **Layer 3 (live LLM-judge evals)** sit behind a `@pytest.mark.eval` marker, run on-demand/nightly via `pytest -m eval` — they're slow (real Claude round-trips) and non-deterministic, so they don't belong in the per-commit loop.

---

## Delivery Order

1. **LangSmith tracing** — one afternoon, no new concepts, immediate payoff for debugging; also produces the traces the eval dataset is harvested from
2. **Layer 1 node tests** — mock LLM calls, test routing and state transitions
3. **Eval dataset** — harvest 3–5 fixtures per AI node from the traces
4. **Layer 3 evals** — LLM-as-judge for the three AI nodes above, gated behind `pytest -m eval`

---

## Full Roadmap

### Phase 3 — Streamlit UI + Real-Time Observability
Build a visual frontend for the agent. New concepts:

- **Streaming LangGraph** — `astream_events` API, real-time node-by-node progress in the browser
- **Streamlit** — the standard frontend for AI demos; upload a spec, watch the graph run live, browse historical reports
- **LangSmith in the UI** — surface trace links per run so failures are one click away from the full LLM call trace

This phase builds directly on Phase 2: LangSmith is already wired in, so the UI just adds a link to traces that already exist. The result is a demo-able artifact that shows well in interviews — visual, live, end-to-end.

### Phase 4 — RAG + RAGAS Evals (standalone project)
A new project: document Q&A or similar, where RAG is the star rather than a supporting feature. Build the system *and* its RAGAS eval suite together. Covers:

- Chunking, embedding, vector databases (ChromaDB or Pinecone)
- Retrieval quality — why naive RAG fails and how to fix it
- RAGAS metrics — relevance, faithfulness, groundedness
- Eval-driven iteration on retrieval and prompts

Arriving at Phase 4 already knowing how evals and LangSmith work means one hard new thing at a time.

---

## Phase 2 Architecture

### Step 0 — Folder cleanup (do first, removes the name clashes)

Before adding anything, untangle the three things currently fighting over the word
"test". This is a small, mechanical rename that makes the rest of Phase 2 unambiguous.

**A — rename agent OUTPUT dir `tests/` → `generated/`** (frees the conventional name)
- One change: `GENERATED_TESTS_DIR = Path("generated")` in `config.py`. Everything else
  routes through that constant, so no other code edits.
- Update `.gitignore` (`tests/` → `generated/`).

**B — drop the `test_` prefix from node modules** (they're nodes, not tests)
- `graph/nodes/test_runner.py` → `runner.py`, `test_planner.py` → `planner.py`,
  `test_generator.py` → `generator.py`. Rename the functions too (`runner`, `planner`,
  `generator`) for consistency.
- Update the 3 imports in `graph/graph_builder.py` and the README mention.

End state — two clearly separated systems. Everything under `evaluation/` tests the
agent; everything else **is** the agent:

```
ai-test-engineer/
│   # ── THE API TESTING AGENT (system under test) ──
├── graph/
│   └── nodes/
│       ├── runner.py            # ← was test_runner.py
│       ├── planner.py           # ← was test_planner.py
│       ├── generator.py         # ← was test_generator.py
│       └── ...                  # spec_parser, failure_analyzer, fix_suggester, report_writer
├── app.py
├── config.py
├── generated/                   # agent OUTPUT — generated tests   [gitignored]  (was tests/)
│
├── **pyproject.toml**           # pytest config (root) — testpaths, marker, addopts
│
│   # ── PHASE 2: THE EVALUATION LAYER (tests the agent) ──
└── **evaluation/**
    ├── conftest.py              # shared fixtures: mock LLM, sample spec, sample state
    ├── **unit/**                # Layer 1 — deterministic, LLM mocked
    │   ├── test_routing.py      # route_after_parse / route_after_run, all branches
    │   ├── test_nodes.py        # each node returns expected state keys
    │   └── test_state.py        # reducers, retry_count cap
    └── **evals/**               # Layer 3 — LLM-as-judge
        ├── datasets/            # committed fixtures, 3–5 per AI node (JSON/YAML)
        │   ├── planner.json
        │   ├── classifier.json
        │   └── fix_suggester.json
        ├── judge.py             # the LLM-judge harness (rubric → Claude → score)
        ├── rubrics.py           # one rubric string per eval
        └── test_evals.py        # @pytest.mark.eval — runs judge against datasets
```

> Why the `test_` prefix stays on `test_routing.py` etc.: those **are** pytest tests, and
> pytest only discovers files matching `test_*.py`. The prefix correctly means "a test."
> The Step 0 rename removed it only from the *node* modules, which are production code, not
> tests. So the prefix now reliably signals one thing: a real test lives here.

### Pytest collection

All test code lives under `evaluation/`, so collection is simple. `pyproject.toml` (at
repo root) points pytest there, registers the marker, and **defaults to skipping evals**
so the per-commit run is Layer 1 only:

```toml
[tool.pytest.ini_options]
testpaths = ["evaluation"]
pythonpath = ["."]                 # so tests can `import graph` / `import config`
addopts = "-m 'not eval'"          # bare `pytest` = Layer 1 unit tests only
markers = [
    "eval: live LLM-as-judge evals (slow, non-deterministic; run with -m eval)",
]
```

- `pytest`            → `evaluation/unit/` only (fast, deterministic, every commit)
- `pytest -m eval`    → `evaluation/evals/` only (on-demand / nightly)

### Layer 1 — mocking strategy

Each node instantiates its LLM **inline** — e.g. `planner` does
`ChatAnthropic(...).with_structured_output(TestPlan)` *inside the function* and imports
`ChatAnthropic` at module top. There is no shared factory, so the mock target is the
**per-module imported symbol**: monkeypatch `graph.nodes.planner.ChatAnthropic` (and the
equivalent in each AI node) to return a stub whose
`.with_structured_output(...).invoke(...)` yields a **fixed Pydantic object**. Tests then
assert on returned state keys and on what `route_*` functions decide — never on LLM quality.

- A `mock_llm` fixture in `evaluation/conftest.py`, parametrised per node's expected schema
- A `sample_state` fixture for hand-built `QAState` dicts to drive routers directly
- Routers (`route_after_parse`, `route_after_run`) are pure functions → test them with
  plain dicts, no mocking needed at all

**Not every node needs a mock.** Only the LLM nodes do — `planner`, `generator`,
`failure_analyzer`, `fix_suggester`. `spec_parser`, `test_runner`, and `report_writer`
are deterministic, so they're tested with plain fixtures (a sample spec, a fake pytest
JSON report) and **no mock at all**.

**Filesystem & cache isolation (required, not optional).** The nodes read/write caches and
write artifacts to `TESTPLAN_DIR`, `REPORTS_DIR`, and `GENERATED_TESTS_DIR`. Behaviour
differs per node, and the tests have to account for it:

- monkeypatch those config path constants to a `tmp_path` for **every** test — so nothing
  touches the repo or pollutes real run dirs
- `spec_parser` and `planner` **cache and skip work on a hit** (planner returns a cached
  plan and never calls the LLM) → start from an **empty cache**, or the test silently
  skips the code under test
- `failure_analyzer` **reads** the test files named in `state["tests"]`, and `fix_suggester`
  **reads and overwrites** them ([fix_suggester.py:80]) → seed real test files in `tmp_path`,
  then assert the file was rewritten and `retry_count` incremented
- for LLM nodes, assert the mocked `ChatAnthropic` was actually invoked when a real call
  was expected (guards against a silent cache-hit false pass)

### Layer 2 — tracing wiring (no code change to nodes)

LangSmith attaches via environment, so instrumentation is config, not a refactor:

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=ai-test-engineer
```

Loaded through the existing `dotenv` in `config.py`. Every `ChatAnthropic` call and graph
node is auto-traced once these are set — nothing in `graph/` changes.

### Layer 3 — judge harness

`evaluation/evals/judge.py` is the reusable core:

```python
def judge(rubric: str, node_input: str, node_output: str) -> Score:
    # one ChatAnthropic call, structured output: {score:int, reasoning:str}
    # called 3x per fixture by the test; caller means the scores
```

- `rubrics.py` holds one rubric per AI node (planner coverage, classifier correctness,
  fix relevance)
- `test_evals.py` loads each `datasets/*.json`, runs the matching node for real, passes
  input+output to `judge()` 3×, asserts mean ≥ 4 (or 100% for the Yes/No classifier)
- Uses a **separate, stronger judge model** constant in `config.py` (e.g. a judge should
  not grade its own family with the same prompt path) — add `JUDGE_MODEL_NAME`

### New dependencies

```
langsmith          # tracing (Layer 1 instrumentation)
pytest-mock        # cleaner mocking for Layer 1 (optional; stdlib unittest.mock works)
```

No new infra — LangSmith is a hosted SaaS, datasets are flat files in-repo.

### Scope of changes to existing code

Phase 2 is mostly **additive**, with one small up-front rename (Step 0):

- **Step 0 rename (mechanical):** `config.py` output-dir constant, `.gitignore`, three
  node filenames + functions, three imports in `graph_builder.py`, README mention. No
  logic changes — pure renames.
- **Additive:** one new top-level `evaluation/` package (with `unit/` and `evals/`),
  `pyproject.toml`, three `LANGSMITH_*` env vars, and a `JUDGE_MODEL_NAME` constant.

Node *logic* (`spec_parser`, `planner`, `runner`, `failure_analyzer`, `fix_suggester`,
`report_writer`) and the graph wiring are not behaviourally modified — the system under
test is renamed and observed, not redesigned.
