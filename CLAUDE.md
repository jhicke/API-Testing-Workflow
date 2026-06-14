# Project instructions for Claude Code

## LLM call permission

**Always ask before running any command that triggers LLM calls.**

This includes:
- `python app.py` (runs the full agent graph)
- `pytest -m eval` (Layer 3 LLM-as-judge evals)
- Any script that instantiates `ChatAnthropic` or invokes the LangGraph graph

Ask: "This will make LLM calls — OK to proceed?" and wait for a yes before running.

Mechanical verification (renames, import fixes, config changes) must be done by reading files and grepping — never by running the agent.
