from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages

from config import MAX_RETRIES
from graph.graph_builder import route_after_run


class TestAddMessagesReducer:
    def test_appends_rather_than_replaces(self):
        existing = [HumanMessage(content="first")]
        incoming = [AIMessage(content="second")]
        result = add_messages(existing, incoming)
        assert len(result) == 2

    def test_empty_existing(self):
        result = add_messages([], [HumanMessage(content="hello")])
        assert len(result) == 1


class TestRetryCountBoundary:
    def test_below_max_retries_continues_loop(self, sample_state):
        sample_state["failures"] = [{"test_name": "test_x"}]
        sample_state["retry_count"] = MAX_RETRIES - 1
        assert route_after_run(sample_state) == "failure_analyzer"

    def test_at_max_retries_exits_loop(self, sample_state):
        sample_state["failures"] = [{"test_name": "test_x"}]
        sample_state["retry_count"] = MAX_RETRIES
        assert route_after_run(sample_state) == "report_writer"
