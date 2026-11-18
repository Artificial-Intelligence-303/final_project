"""A finished example: a team that triages a support inbox. Provided, to read.

Your `team.py` follows the same shape for your own task, which cannot be
this one. Try it with:

    uv run python src/example_inbox.py team "How many report a crash?"
    uv run python src/example_inbox.py single "How many report a crash?"

The inbox holds 300 messages from students using CampusBite, an invented
campus dining app. The person is the app's developer, who asks how many
people report a problem and which bugs to file.

The team divides the reading, and mixes two models:

- Lead, on the evaluation's model, plans the work, adds up the counts, and
  files bugs. It does not read the messages itself.
- Reader, fixed to glm-5.3-flash, the cheapest model, reads one batch of up
  to 50 messages and counts it by category. The lead calls it once per
  batch, in parallel, and each call starts a fresh conversation.
- Checker, fixed to glm-5.3-flash, reads the messages a proposed bug cites
  and the bugs already filed, and says whether to file it.

The single agent has the same four tools and reads the inbox itself, so
each message it reads stays in its one conversation while it counts.
"""

import json
import sys
from pathlib import Path

from agents import Agent

import run as runner
from model import model
from run import ask_person, run, tool

DATA = Path(__file__).parent.parent / "example_data"
TICKETS = json.loads((DATA / "tickets.json").read_text())
FILED = json.loads((DATA / "filed_bugs.json").read_text())
BATCH = 50
CATEGORIES = (
    "The categories are: login (cannot sign in, codes, signed out), payment "
    "(charges, declines, refunds, meal swipes), android crash (the app "
    "closes or will not open on Android), wrong hours (a dining hall's hours "
    "in the app are wrong), missing order (marked ready but not there), "
    "slow (loading or lag), feature request, praise, and other. Judge each "
    "message by what it says, not by its subject line. "
)

# The bugs filed during a run. Each run starts with none.
new_bugs: list[dict] = []


def start_fresh() -> None:
    """Forget the bugs filed in an earlier run."""
    new_bugs.clear()


@tool
def count_tickets() -> str:
    """How many messages the inbox holds, numbered from 1."""
    return f"{len(TICKETS)} messages, numbered 1 to {len(TICKETS)}"


@tool
def read_tickets(first: int, last: int) -> str:
    """Read the messages numbered first to last, at most 50 at a time.

    Args:
        first: the number of the first message to read.
        last: the number of the last message to read.
    """
    if not 1 <= first <= last <= len(TICKETS):
        raise ValueError(
            f"messages are numbered 1 to {len(TICKETS)}, and first must not "
            "be after last"
        )
    if last - first + 1 > BATCH:
        raise ValueError(f"read at most {BATCH} messages at a time")
    return "\n".join(
        f"#{t['id']} | {t['device']} | {t['subject']}: {t['message']}"
        for t in TICKETS[first - 1 : last]
    )


@tool
def filed_bugs() -> str:
    """The bugs already filed, so the same problem is not filed twice."""
    bugs = FILED + new_bugs
    return "\n".join(f"{b['id']}: {b['title']}" for b in bugs)


@tool
def file_bug(title: str, ticket_ids: list[int], summary: str) -> str:
    """File a bug report, after the developer approves.

    Args:
        title: a short title naming the problem.
        ticket_ids: the numbers of at least three messages that report it.
        summary: what users report, in two or three sentences.
    """
    if len(set(ticket_ids)) < 3:
        raise ValueError("cite at least three different messages")
    unknown = [n for n in ticket_ids if not 1 <= n <= len(TICKETS)]
    if unknown:
        raise ValueError(
            f"no messages numbered {unknown}; they run 1 to {len(TICKETS)}"
        )
    if not ask_person(f"File bug '{title}' citing {len(ticket_ids)} messages?"):
        return "The developer declined. No bug was filed."
    bug = {"id": f"BUG-{13 + len(new_bugs)}", "title": title}
    new_bugs.append(bug)
    return f"filed {bug['id']}: {title}"


def build_team() -> Agent:
    """Return the lead, which reaches the reader and the checker."""
    start_fresh()
    reader = Agent(
        name="Reader",
        instructions=(
            "You read one batch of support messages for a campus dining app "
            "and sort them. Call read_tickets once for the range you are "
            "given. "
            + CATEGORIES
            + "Reply with one line per category: the category, the number of "
            "messages in it, and their numbers, such as 'payment: 3 (#4, #9, "
            "#12)'. Count carefully; the counts must add up to the batch size."
        ),
        tools=[read_tickets],
        model=model("glm-5.3-flash"),
    )
    checker = Agent(
        name="Checker",
        instructions=(
            "You check a proposed bug report before it is filed. Call "
            "filed_bugs, then read_tickets for at least three of the "
            "messages it cites, one range per message. Answer FILE if the "
            "messages report the problem in the title and no filed bug "
            "already covers it. Otherwise answer DO NOT FILE and say why."
        ),
        tools=[filed_bugs, read_tickets],
        model=model("glm-5.3-flash"),
    )
    return Agent(
        name="Lead",
        instructions=(
            "You help the developer of a campus dining app understand their "
            "support inbox. You do not read messages yourself. Call "
            "count_tickets, then split the inbox into batches of 50 and call "
            "read_batch once for each batch, all in the same turn. Add up "
            "the readers' counts for each category, and use their message "
            "numbers when you need examples. Before filing a bug, call "
            "check_bug with the title and the message numbers, and file only "
            "if the checker says FILE. File with file_bug, which asks the "
            "developer. If the developer declines, stop. Answer with the "
            "numbers you found."
        ),
        tools=[
            count_tickets,
            reader.as_tool(
                "read_batch",
                "Read and count one batch of messages. Give the first and "
                "last message numbers, at most 50 apart.",
            ),
            checker.as_tool(
                "check_bug",
                "Check a proposed bug: give its title and the message "
                "numbers it cites.",
            ),
            file_bug,
        ],
        model=model(),
    )


def build_single() -> Agent:
    """Return one agent with the team's four tools and no other agents."""
    start_fresh()
    return Agent(
        name="Triage",
        instructions=(
            "You help the developer of a campus dining app understand their "
            "support inbox. Call count_tickets, then read the inbox with "
            "read_tickets, 50 messages at a time, and sort each message. "
            + CATEGORIES
            + "Count carefully. Before filing a bug, call filed_bugs and "
            "reread at least three of the messages it cites, and file only "
            "if they report the problem and no filed bug already covers it. "
            "File with file_bug, which asks the developer. If the developer "
            "declines, stop. Answer with the numbers you found."
        ),
        tools=[count_tickets, read_tickets, filed_bugs, file_bug],
        model=model(),
    )


if __name__ == "__main__":
    # The example keeps its own log, so it never counts toward your checks.
    runner.LOG = runner.LOG.with_name("example-runs.jsonl")
    design = sys.argv[1] if len(sys.argv) > 1 else "team"
    lead = build_team() if design == "team" else build_single()
    task = " ".join(sys.argv[2:]) or "How many messages report a crash?"
    print(run(lead, task, design))
