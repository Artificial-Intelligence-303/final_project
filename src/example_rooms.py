"""A finished example: a team that books study rooms. Provided, to read.

Your `team.py` follows the same shape for your own task. Try it with:

    uv run python src/example_rooms.py team "Book me a room Wednesday"
    uv run python src/example_rooms.py single "Book me a room Wednesday"

The team has four agents. The desk agent talks to the student. It calls the
finder and the checker as tools, and hands the conversation to the booker
once the student has chosen a room. The single agent has the same two tools
and does all of it alone.
"""

import sys

from agents import Agent

import run as runner
from model import model
from run import ask_person, run, tool

FREE = {
    "monday": ["Room A at 10am", "Room C at 1pm"],
    "wednesday": ["Room B at 2pm", "Room C at 3pm"],
    "friday": [],
}
BOOKED: list[str] = []


@tool
def free_rooms(day: str) -> str:
    """List the study rooms that are free on a day, such as "Wednesday"."""
    rooms = FREE.get(day.strip().lower())
    if rooms is None:
        raise ValueError(f"no schedule for {day}; use a weekday name")
    return ", ".join(rooms) or "none free"


@tool
def book(day: str, slot: str) -> str:
    """Book a free slot, given exactly as free_rooms lists it."""
    if slot not in FREE.get(day.strip().lower(), []):
        raise ValueError(f"{slot} is not free on {day}; call free_rooms")
    if not ask_person(f"Book {slot} on {day}?"):
        return "The student declined this booking."
    BOOKED.append(f"{day}: {slot}")
    return f"booked {slot} on {day}"


def build_team() -> Agent:
    """Return the desk agent, which reaches the other three."""
    finder = Agent(
        name="Finder",
        instructions=(
            "You find free study rooms. Given a day, call free_rooms and "
            "report the free slots exactly as listed."
        ),
        tools=[free_rooms],
        model=model(),
    )
    checker = Agent(
        name="Checker",
        instructions=(
            "You check a proposed booking before it is made. Call free_rooms "
            "for the day and say whether the slot is listed and whether it "
            "matches what the student asked for. Answer OK, or say what is "
            "wrong."
        ),
        tools=[free_rooms],
        model=model(),
    )
    booker = Agent(
        name="Booker",
        instructions=(
            "You book the slot the student chose, with the book tool, then "
            "confirm it. If the student declines, say so and stop."
        ),
        tools=[book],
        model=model(),
    )
    return Agent(
        name="Desk",
        instructions=(
            "You help a student book a study room. Ask the finder for free "
            "slots, choose the one that fits the request, and ask the checker "
            "to check it. Once it is checked, hand off to the booker."
        ),
        tools=[
            finder.as_tool("find_rooms", "Find the free slots on a day."),
            checker.as_tool("check_booking", "Check a proposed booking."),
        ],
        handoffs=[booker],
        model=model(),
    )


def build_single() -> Agent:
    """Return one agent with the same tools and no other agents."""
    return Agent(
        name="Room helper",
        instructions=(
            "You help a student book a study room. Find the free slots, "
            "choose the one that fits the request, check it, and book it."
        ),
        tools=[free_rooms, book],
        model=model(),
    )


if __name__ == "__main__":
    # The example keeps its own log, so it never counts toward your checks.
    runner.LOG = runner.LOG.with_name("example-runs.jsonl")
    design = sys.argv[1] if len(sys.argv) > 1 else "team"
    lead = build_team() if design == "team" else build_single()
    task = " ".join(sys.argv[2:]) or "Book me a room Wednesday"
    print(run(lead, task, design))
