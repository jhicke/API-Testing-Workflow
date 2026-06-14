from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from config import MAX_RETRIES
from graph.nodes.failure_analyzer import failure_analyzer
from graph.nodes.fix_suggester import fix_suggester
from graph.nodes.report_writer import report_writer
from graph.nodes.spec_parser import spec_parser
from graph.nodes.test_generator import test_generator
from graph.nodes.test_planner import test_planner
from graph.nodes.test_runner import test_runner
from graph.state import QAState


def route_after_parse(state: QAState) -> str:
    if state.get("error"):
        return "report_writer"
    if state.get("tests"):          # cache hit — tests already loaded
        return "test_runner"
    return "test_planner"


def route_after_run(state: QAState) -> str:
    if state.get("error"):
        return "report_writer"
    if not state.get("failures"):
        return "report_writer"
    if state["retry_count"] >= MAX_RETRIES:
        return "report_writer"
    return "failure_analyzer"


def build_graph(review_mode: bool = False):
    builder = StateGraph(QAState)

    # Register every node
    builder.add_node("spec_parser", spec_parser)
    builder.add_node("test_planner", test_planner)
    builder.add_node("test_generator", test_generator)
    builder.add_node("test_runner", test_runner)
    builder.add_node("failure_analyzer", failure_analyzer)
    builder.add_node("fix_suggester", fix_suggester)
    builder.add_node("report_writer", report_writer)

    # Entry point
    builder.set_entry_point("spec_parser")

    # Edges
    builder.add_conditional_edges("spec_parser", route_after_parse)
    builder.add_edge("test_planner", "test_generator")
    builder.add_edge("test_generator", "test_runner")
    builder.add_conditional_edges("test_runner", route_after_run)
    builder.add_edge("failure_analyzer", "fix_suggester")
    builder.add_edge("fix_suggester", "test_runner")
    builder.add_edge("report_writer", END)

    if review_mode:
        return builder.compile(
            checkpointer=MemorySaver(),
            interrupt_before=["test_runner"],
        )

    return builder.compile()
