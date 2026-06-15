from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from config import JUDGE_MODEL_NAME


class Score(BaseModel):
    score: int
    reasoning: str


def judge(rubric: str, node_input: str, node_output: str) -> Score:
    llm = ChatAnthropic(model=JUDGE_MODEL_NAME, temperature=0, max_tokens=1024)
    structured_llm = llm.with_structured_output(Score)

    prompt = f"""You are an expert QA evaluator. Score the following AI output on a scale of 1-5.

Rubric:
{rubric}

Node input:
{node_input}

Node output:
{node_output}

Return a score from 1 to 5 and your reasoning.
1 = completely wrong or missing
3 = partially correct but significant issues
5 = correct and complete
"""
    return structured_llm.invoke(prompt)
