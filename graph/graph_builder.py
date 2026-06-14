from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from config import MAX_RETRIES
from graph.nodes.failure_analyzer import failure_analyzer
from graph.nodes.fix_suggester import fix_suggester
from graph.nodes.generator import generator
from graph.nodes.planner import planner
from graph.nodes.report_writer import report_writer
from graph.nodes.runner import runner
from graph.nodes.spec_parser import spec_parser
from graph.state import QAState


def route_after_parse(state: QAState) -> str:
    if state.get("error"):
        return "report_writer"
    if state.get("tests"):          # cache hit — tests already loaded
        return "runner"
    return "planner"


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

    builder.add_node("spec_parser", spec_parser)
    builder.add_node("planner", planner)
    builder.add_node("generator", generator)
    builder.add_node("runner", runner)
    builder.add_node("failure_analyzer", failure_analyzer)
    builder.add_node("fix_suggester", fix_suggester)
    builder.add_node("report_writer", report_writer)

    builder.set_entry_point("spec_parser")

    builder.add_conditional_edges("spec_parser", route_after_parse)
    builder.add_edge("planner", "generator")
    builder.add_edge("generator", "runner")
    builder.add_conditional_edges("runner", route_after_run)
    builder.add_edge("failure_analyzer", "fix_suggester")
    builder.add_edge("fix_suggester", "runner")
    builder.add_edge("report_writer", END)

    if review_mode:
        return builder.compile(
            checkpointer=MemorySaver(),
            interrupt_before=["runner"],
        )

    return builder.compile()
