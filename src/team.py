"""Your team of agents, and the single agent you compare it with.

Write your tools here as functions decorated with `@tool` from `run`, each
with type hints and a docstring the model reads. A tool that changes something
calls `ask_person` before it acts. A tool that rejects a bad call raises
`ValueError` with a message the model can act on.

`src/example_inbox.py` is a finished example of this file's shape.
"""

from agents import Agent


def build_team() -> Agent:
    """Return the lead agent of your team.

    The lead reaches the other agents through handoffs, through agent tools
    made with `agent.as_tool(...)`, or both.
    """
    raise NotImplementedError("TODO: build your team")


def build_single() -> Agent:
    """Return one agent with your team's tools and no other agents."""
    raise NotImplementedError("TODO: build your single agent")
