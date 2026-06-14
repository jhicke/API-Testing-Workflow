#!/usr/bin/env python3
"""AI Test Engineer — autonomous QA agent powered by LangGraph + Claude."""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def _resolve_reuse_tests(generated_tests_dir: Path) -> list[str]:
    """Return test file paths from tests/, or [] if none exist."""
    test_files = sorted(str(p) for p in generated_tests_dir.glob("test_*.py"))
    if not test_files:
        print(f"Warning: no test files found in {generated_tests_dir}", file=sys.stderr)
    else:
        print(f"  Reusing existing tests from {generated_tests_dir}")
    return test_files


def main():
    parser = argparse.ArgumentParser(
        description="AI Test Engineer: ingest an OpenAPI spec and autonomously run QA"
    )
    parser.add_argument(
        "spec",
        help="Path to OpenAPI spec file (JSON or YAML)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Pause before running tests so generated files can be reviewed first",
    )
    parser.add_argument(
        "--reuse-tests",
        action="store_true",
        help="Skip generation and reuse existing tests from tests/",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    from config import GENERATED_TESTS_DIR
    from graph.graph_builder import build_graph

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Pre-load existing tests if --reuse-tests was passed
    preloaded_tests: list[str] = []
    if args.reuse_tests:
        preloaded_tests = _resolve_reuse_tests(GENERATED_TESTS_DIR)
        if not preloaded_tests:
            print("Error: no existing tests found to reuse.", file=sys.stderr)
            sys.exit(1)

    initial_state = {
        "spec": {"path": str(spec_path)},
        "plan": [],
        "tests": preloaded_tests,
        "results": {},
        "failures": [],
        "fixes": [],
        "messages": [],
        "retry_count": 0,
        "run_id": run_id,
        "spec_hash": "",
        "error": "",
    }

    graph = build_graph(review_mode=args.review)

    print(f"\nStarting QA run {run_id}...")

    if args.review:
        config = {"configurable": {"thread_id": run_id}}

        # Run up to the interrupt point (before test_runner)
        for step in graph.stream(initial_state, config=config, stream_mode="updates"):
            node_name = list(step.keys())[0]
            print(f"  ✓ {node_name}")

        print("\n--- REVIEW PAUSE ---")
        print("Generated test files are ready. Press Enter to run them, or Ctrl+C to abort.\n")

        try:
            input()
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)

        # Resume from the checkpoint
        for step in graph.stream(None, config=config, stream_mode="updates"):
            node_name = list(step.keys())[0]
            print(f"  ✓ {node_name}")

    else:
        for step in graph.stream(initial_state, stream_mode="updates"):
            node_name = list(step.keys())[0]
            print(f"  ✓ {node_name}")


if __name__ == "__main__":
    main()
