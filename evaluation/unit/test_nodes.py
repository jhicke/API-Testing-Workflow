from unittest.mock import MagicMock

import pytest

from graph.nodes.failure_analyzer import FailureAnalysis, FailureReport, failure_analyzer
from graph.nodes.fix_suggester import FileFix, FixSet, fix_suggester
from graph.nodes.planner import Plan, PlanCase, planner


class TestPlannerNode:
    def test_short_circuits_on_error(self, sample_state):
        sample_state["error"] = "spec failed"
        assert planner(sample_state) == {}

    def test_returns_plan_and_calls_llm(self, sample_state, monkeypatch, tmp_path):
        monkeypatch.setattr("graph.nodes.planner.PLAN_CACHE_FILE", tmp_path / ".cache.json")
        monkeypatch.setattr("graph.nodes.planner.PLAN_FILE", tmp_path / "test_plan.json")
        monkeypatch.setattr("graph.nodes.planner.TESTPLAN_DIR", tmp_path)
        monkeypatch.setattr("graph.nodes.planner.REPORTS_DIR", tmp_path / "reports")

        fake_plan = Plan(cases=[
            PlanCase(
                endpoint_path="/todos",
                method="GET",
                scenario="happy_path",
                description="Get all todos",
                expected_status=200,
                test_data={},
            )
        ])
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = fake_plan
        monkeypatch.setattr("graph.nodes.planner.ChatAnthropic", MagicMock(return_value=mock_llm))

        result = planner(sample_state)

        assert "plan" in result
        assert len(result["plan"]) == 1
        assert result["plan"][0]["endpoint_path"] == "/todos"
        mock_llm.with_structured_output.return_value.invoke.assert_called_once()


class TestFailureAnalyzerNode:
    def test_short_circuits_on_error(self, sample_state):
        sample_state["error"] = "runner crashed"
        assert failure_analyzer(sample_state) == {}

    def test_short_circuits_on_empty_failures(self, sample_state):
        sample_state["failures"] = []
        assert failure_analyzer(sample_state) == {}

    def test_returns_enriched_failures_and_calls_llm(self, sample_state, monkeypatch):
        sample_state["failures"] = [{"test_name": "test_get_todo_happy_path", "reason": "AssertionError"}]

        fake_report = FailureReport(analyses=[
            FailureAnalysis(
                test_name="test_get_todo_happy_path",
                failure_type="test_bug",
                reason="Wrong expected status code",
                suggested_fix="Change expected_status to 200",
            )
        ])
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = fake_report
        monkeypatch.setattr("graph.nodes.failure_analyzer.ChatAnthropic", MagicMock(return_value=mock_llm))

        result = failure_analyzer(sample_state)

        assert "failures" in result
        assert result["failures"][0]["failure_type"] == "test_bug"
        mock_llm.with_structured_output.return_value.invoke.assert_called_once()


class TestFixSuggesterNode:
    def test_short_circuits_on_error(self, sample_state):
        sample_state["error"] = "something broke"
        assert fix_suggester(sample_state) == {}

    def test_increments_retry_when_no_fixable_failures(self, sample_state):
        # backend_bug failures are not fixable — node should still bump retry_count
        sample_state["failures"] = [{"failure_type": "backend_bug", "test_name": "test_x"}]
        sample_state["retry_count"] = 1
        assert fix_suggester(sample_state) == {"retry_count": 2}

    def test_applies_fix_increments_retry_and_overwrites_file(self, sample_state, monkeypatch, tmp_path):
        test_file = tmp_path / "test_todos.py"
        test_file.write_text("def test_placeholder(): pass")

        sample_state["failures"] = [{
            "test_name": "test_get_todo",
            "failure_type": "test_bug",
            "file_path": str(test_file),
            "suggested_fix": "Change status code to 200",
        }]
        sample_state["tests"] = [str(test_file)]
        sample_state["retry_count"] = 0

        fake_fix_set = FixSet(fixes=[
            FileFix(
                filename="test_todos.py",
                fixed_content="def test_placeholder(): assert True",
                changes_summary="Fixed status code assertion",
            )
        ])
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = fake_fix_set
        monkeypatch.setattr("graph.nodes.fix_suggester.ChatAnthropic", MagicMock(return_value=mock_llm))

        result = fix_suggester(sample_state)

        assert result["retry_count"] == 1
        assert len(result["fixes"]) == 1
        assert test_file.read_text() == "def test_placeholder(): assert True"
