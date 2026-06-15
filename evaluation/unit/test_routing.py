import pytest

from config import MAX_RETRIES
from graph.graph_builder import route_after_parse, route_after_run


class TestRouteAfterParse:
    def test_error_goes_to_report_writer(self, sample_state):
        sample_state["error"] = "spec failed to parse"
        assert route_after_parse(sample_state) == "report_writer"

    def test_cache_hit_goes_to_runner(self, sample_state):
        # tests already populated means a cache hit — skip planner/generator
        sample_state["tests"] = ["generated/test_todos.py"]
        assert route_after_parse(sample_state) == "runner"

    def test_no_cache_goes_to_planner(self, sample_state):
        assert route_after_parse(sample_state) == "planner"

    def test_error_takes_priority_over_cache_hit(self, sample_state):
        sample_state["error"] = "something broke"
        sample_state["tests"] = ["generated/test_todos.py"]
        assert route_after_parse(sample_state) == "report_writer"


class TestRouteAfterRun:
    def test_error_goes_to_report_writer(self, sample_state):
        sample_state["error"] = "runner crashed"
        assert route_after_run(sample_state) == "report_writer"

    def test_no_failures_goes_to_report_writer(self, sample_state):
        sample_state["failures"] = []
        assert route_after_run(sample_state) == "report_writer"

    def test_failures_go_to_failure_analyzer(self, sample_state):
        sample_state["failures"] = [{"test": "test_get_todo", "reason": "404"}]
        assert route_after_run(sample_state) == "failure_analyzer"

    def test_retries_exhausted_goes_to_report_writer(self, sample_state):
        sample_state["failures"] = [{"test": "test_get_todo", "reason": "404"}]
        sample_state["retry_count"] = MAX_RETRIES
        assert route_after_run(sample_state) == "report_writer"

    def test_error_takes_priority_over_failures(self, sample_state):
        sample_state["error"] = "runner crashed"
        sample_state["failures"] = [{"test": "test_get_todo", "reason": "404"}]
        assert route_after_run(sample_state) == "report_writer"
