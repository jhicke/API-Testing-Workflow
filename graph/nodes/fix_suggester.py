import json
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import MAX_TOKENS, MODEL_NAME
from graph.state import QAState


class FileFix(BaseModel):
    filename: str
    fixed_content: str
    changes_summary: str


class FixSet(BaseModel):
    fixes: list[FileFix]


def fix_suggester(state: QAState) -> dict:
    if state.get("error"):
        return {}

    fixable = [f for f in state.get("failures", []) if f.get("failure_type") == "test_bug"]

    if not fixable:
        # No fixable failures — increment retry so the loop exits cleanly
        return {"retry_count": state["retry_count"] + 1}

    # Group fixable failures by filename
    by_file: dict[str, list] = {}
    for failure in fixable:
        fname = Path(failure.get("file_path", "")).name
        if fname:
            by_file.setdefault(fname, []).append(failure)

    # Read current content of each file that needs fixing
    file_contents: dict[str, str] = {}
    for test_path in state.get("tests", []):
        p = Path(test_path)
        if p.exists() and p.name in by_file:
            file_contents[p.name] = p.read_text(encoding="utf-8")

    fixes_needed = {
        fname: [f["suggested_fix"] for f in failures]
        for fname, failures in by_file.items()
    }

    llm = ChatAnthropic(model=MODEL_NAME, temperature=0, max_tokens=MAX_TOKENS)
    structured_llm = llm.with_structured_output(FixSet)

    prompt = f"""You are a pytest expert fixing failing test files.

Current file contents:
{json.dumps(file_contents, indent=2)}

Required fixes per file:
{json.dumps(fixes_needed, indent=2)}

Rules:
- Return the COMPLETE fixed file content for each file — not just the changed lines
- Only fix test_bug issues: wrong URLs, wrong status codes, wrong assertions, syntax errors
- Do NOT weaken assertions or remove checks to make a test pass
- Do NOT change tests that are currently passing
- Keep all imports and test structure intact
"""

    try:
        result = structured_llm.invoke(prompt)
    except Exception as e:
        return {"error": f"fix_suggester failed: {e}", "retry_count": state["retry_count"] + 1}

    applied_fixes = list(state.get("fixes", []))

    for fix in result.fixes:
        for test_path in state.get("tests", []):
            p = Path(test_path)
            if p.name == fix.filename:
                p.write_text(fix.fixed_content, encoding="utf-8")
                applied_fixes.append({
                    "retry": state["retry_count"] + 1,
                    "filename": fix.filename,
                    "changes": fix.changes_summary,
                })
                break

    return {
        "fixes": applied_fixes,
        "retry_count": state["retry_count"] + 1,
    }
