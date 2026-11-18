"""Running a task, asking a person, and logging the run. Provided; do not edit.

`run` gives a task to an agent, with a step limit, and writes one line to
`logs/runs.jsonl` describing what happened: which agents acted, each tool
call and its result, each handoff, each approval a person gave or refused,
the tokens used and the time taken.
"""

import datetime
import json
import time
from pathlib import Path

from agents import Agent, MaxTurnsExceeded, Runner, function_tool
from openai import APIStatusError

import model as models
from model import model_name

LOG = Path(__file__).parent.parent / "logs" / "runs.jsonl"
MAX_TURNS = 15

_approvals: list[dict[str, object]] = []

# During an evaluation, main.py sets this to "approve" or "decline" from the
# task's line in docs/tasks.txt, and ask_person answers with it.
scripted_answer: str | None = None


def ask_person(question: str) -> bool:
    """Ask the person at the keyboard to approve an action; True if they do.

    Call this inside any tool that changes something, before it acts. The
    question and the answer are saved with the run.
    """
    if scripted_answer is not None:
        approved = scripted_answer == "approve"
        print(f"\n{question} Approve? [y/n] {'y' if approved else 'n'}")
        _approvals.append({"question": question, "approved": approved})
        return approved
    answer = input(f"\n{question} Approve? [y/n] ").strip().lower()
    approved = answer in ("y", "yes")
    _approvals.append({"question": question, "approved": approved})
    return approved


def error_result(context: object, error: Exception) -> str:
    """The result the model reads when one of your tools raises an error.

    A ValueError's message reaches the model, so it can correct the call.
    Any other error is reported without its details.
    """
    if isinstance(error, ValueError):
        return f"error: {error}"
    return "error: the tool failed"


def tool(function):
    """Make a function a tool the model can call.

    Use it as `@tool` above the function. The function's name, type hints
    and docstring become the tool specification, and a ValueError it raises
    reaches the model as a result starting "error:". The plain function
    stays reachable as `.function`, so a test can call
    `save_dinner.function("Monday", "Spinach Dal")`.
    """
    made = function_tool(function, failure_error_function=error_result)
    made.function = function
    return made


def is_agent_tool(candidate: object) -> bool:
    """True if a tool is another agent, made with `agent.as_tool(...)`."""
    return bool(getattr(candidate, "_is_agent_tool", False))


def agents_in(lead: Agent) -> list[Agent]:
    """The agents reachable from the lead, through handoffs or agent tools."""
    found: list[Agent] = []
    waiting = [lead]
    while waiting:
        agent = waiting.pop(0)
        if any(agent is seen for seen in found):
            continue
        found.append(agent)
        for other in agent.handoffs:
            if isinstance(other, Agent):
                waiting.append(other)
        for offered in agent.tools:
            if is_agent_tool(offered):
                waiting.append(offered._agent_instance)
    return found


def own_tools(lead: Agent) -> list[str]:
    """The names of the tools on a team that are not other agents."""
    names = []
    for agent in agents_in(lead):
        for offered in agent.tools:
            if not is_agent_tool(offered) and offered.name not in names:
                names.append(offered.name)
    return names


def _steps(result: object, agent_tools: dict[str, str]) -> list[dict[str, str]]:
    """One entry per thing that happened in a run, in order."""
    steps = []
    for item in result.new_items:
        kind = type(item).__name__
        agent = getattr(getattr(item, "agent", None), "name", "")
        raw = getattr(item, "raw_item", None)
        if kind == "ToolCallItem":
            name = getattr(raw, "name", "")
            label = "agent call" if name in agent_tools else "tool call"
            arguments = str(getattr(raw, "arguments", ""))
            steps.append(
                {
                    "agent": agent,
                    "kind": label,
                    "name": name,
                    "text": arguments[:300],
                }
            )
        elif kind == "ToolCallOutputItem":
            steps.append(
                {
                    "agent": agent,
                    "kind": "result",
                    "name": "",
                    "text": str(item.output)[:300],
                }
            )
        elif kind == "HandoffOutputItem":
            target = getattr(getattr(item, "target_agent", None), "name", "")
            steps.append(
                {"agent": agent, "kind": "handoff", "name": target, "text": ""}
            )
        elif kind == "MessageOutputItem":
            steps.append(
                {
                    "agent": agent,
                    "kind": "message",
                    "name": "",
                    "text": _message_text(raw)[:300],
                }
            )
    return steps


def _message_text(raw: object) -> str:
    """The text of a message the model wrote."""
    parts = getattr(raw, "content", []) or []
    return " ".join(getattr(part, "text", "") for part in parts).strip()


def run(lead: Agent, task: str, design: str) -> str:
    """Give a task to an agent, log the run, and return its final answer.

    Args:
        lead: the agent that receives the task: your team's lead agent, or
            your single agent.
        task: the request, as the person would type it.
        design: "team" or "single", recorded in the log.
    """
    _approvals.clear()
    models.usage_by_model.clear()
    agent_tools = {
        offered.name: offered._agent_instance.name
        for agent in agents_in(lead)
        for offered in agent.tools
        if is_agent_tool(offered)
    }
    record: dict[str, object] = {
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        "design": design,
        "task": task,
        "model": model_name(),
        "lead": lead.name,
    }
    start = time.monotonic()
    try:
        result = Runner.run_sync(lead, task, max_turns=MAX_TURNS)
    except (MaxTurnsExceeded, APIStatusError) as problem:
        if isinstance(problem, MaxTurnsExceeded):
            answer = f"stopped: the step limit of {MAX_TURNS} was reached"
        else:
            answer = (
                f"stopped: the model service answered {problem.status_code}: "
                f"{problem.message}"
            )
        record.update(
            error=answer,
            steps=[],
            agents_at_work=[],
            requests=0,
            input_tokens=0,
            output_tokens=0,
        )
    else:
        answer = str(result.final_output)
        steps = _steps(result, agent_tools)
        usage = result.context_wrapper.usage
        acted = {step["agent"] for step in steps if step["agent"]}
        acted |= {step["name"] for step in steps if step["kind"] == "handoff"}
        acted |= {
            agent_tools[s["name"]] for s in steps if s["kind"] == "agent call"
        }
        record.update(
            error="",
            steps=steps,
            agents_at_work=sorted(acted),
            requests=usage.requests,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )
    record["tokens_by_model"] = {
        name: {"input": counts[0], "output": counts[1]}
        for name, counts in models.usage_by_model.items()
    }
    # Count from each model, so a run stopped by the step limit counts too.
    record["input_tokens"] = sum(c[0] for c in models.usage_by_model.values())
    record["output_tokens"] = sum(c[1] for c in models.usage_by_model.values())
    spent = models.cost(models.usage_by_model)
    record["cost"] = round(spent, 6) if spent is not None else None
    record["approvals"] = list(_approvals)
    record["seconds"] = round(time.monotonic() - start, 1)
    record["answer"] = answer[:1000]
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a") as handle:
        handle.write(json.dumps(record) + "\n")
    return answer
