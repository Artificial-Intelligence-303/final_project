"""Run a task, run your evaluation, or summarize the log. Provided.

Examples:
    uv run python src/main.py team "Find me a free room on Wednesday"
    uv run python src/main.py single "Find me a free room on Wednesday"
    uv run python src/main.py eval glm-5.3-flash
    uv run python src/main.py log

`team` and `single` use the model named by MODEL in `.env`, or glm-5.3-flash.
`eval` runs on each model named after it, one after another.
"""

import json
import os
import sys
from pathlib import Path

import run as runner
import team
from run import LOG, run

TASKS = Path(__file__).parent.parent / "docs" / "tasks.txt"
TRIALS = 3
ANSWERS = ("approve", "decline")


def task_lines() -> list[tuple[str, str | None]]:
    """Each task in docs/tasks.txt, with its approval answer if it has one.

    A line is the request as the person would type it, optionally followed
    by `| approve` or `| decline`, the answer to give if the team asks.
    """
    lines = TASKS.read_text().splitlines() if TASKS.exists() else []
    found = []
    for line in lines:
        request, _, answer = line.partition("|")
        answer = answer.strip().lower()
        if request.strip():
            scripted = answer if answer in ANSWERS else None
            found.append((request.strip(), scripted))
    return found


def build(design: str):
    """Your team's lead agent, or your single agent."""
    return team.build_team() if design == "team" else team.build_single()


def evaluate(models: list[str]) -> None:
    """Run each task three times with the team and three with one agent.

    The runs repeat on each model in `models`, or on the model in `.env` if
    none is named.
    """
    for name in models or [""]:
        if name:
            os.environ["MODEL"] = name
        for number, (task, answer) in enumerate(task_lines(), start=1):
            runner.scripted_answer = answer
            for design in ("team", "single"):
                for trial in range(1, TRIALS + 1):
                    print(
                        f"\n{name or 'model in .env'}, task {number}, "
                        f"{design}, trial {trial}: {task}"
                    )
                    print(run(build(design), task, design))
        runner.scripted_answer = None


def summarize() -> None:
    """Print each task's runs, tokens and time, by model and design."""
    if not LOG.exists():
        print("No runs logged yet.")
        return
    rows = [json.loads(line) for line in LOG.read_text().splitlines() if line]
    print(
        f"{'model':22} {'design':7} {'runs':>4} {'tokens':>8} {'seconds':>8} "
        f"{'stopped':>8}  task"
    )
    for name in dict.fromkeys(row["model"] for row in rows):
        for task in dict.fromkeys(row["task"] for row in rows):
            for design in ("team", "single"):
                mine = [
                    r
                    for r in rows
                    if r["model"] == name
                    and r["task"] == task
                    and r["design"] == design
                ]
                if not mine:
                    continue
                tokens = sum(
                    r["input_tokens"] + r["output_tokens"] for r in mine
                )
                seconds = sum(r["seconds"] for r in mine)
                stopped = sum(1 for r in mine if r["error"])
                print(
                    f"{name:22} {design:7} {len(mine):>4} "
                    f"{tokens // len(mine):>8} {seconds / len(mine):>8.1f} "
                    f"{stopped:>8}  {task[:50]}"
                )


def main() -> None:
    """Read the command and do it."""
    if len(sys.argv) >= 3 and sys.argv[1] in ("team", "single"):
        print(run(build(sys.argv[1]), " ".join(sys.argv[2:]), sys.argv[1]))
    elif sys.argv[1:2] == ["eval"]:
        evaluate(sys.argv[2:])
    elif sys.argv[1:] == ["log"]:
        summarize()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
