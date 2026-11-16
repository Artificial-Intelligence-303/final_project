"""Run a task, run your evaluation, or summarize the log. Provided.

Examples:
    uv run python src/main.py team "Find me a free room on Wednesday"
    uv run python src/main.py single "Find me a free room on Wednesday"
    uv run python src/main.py eval
    uv run python src/main.py log
"""

import json
import sys
from pathlib import Path

import team
from run import LOG, run

TASKS = Path(__file__).parent.parent / "docs" / "tasks.txt"
TRIALS = 3


def tasks() -> list[str]:
    """The evaluation tasks in docs/tasks.txt, one per line."""
    lines = TASKS.read_text().splitlines() if TASKS.exists() else []
    return [line.strip() for line in lines if line.strip()]


def build(design: str):
    """Your team's lead agent, or your single agent."""
    return team.build_team() if design == "team" else team.build_single()


def evaluate() -> None:
    """Run each task three times with the team and three with one agent."""
    for number, task in enumerate(tasks(), start=1):
        for design in ("team", "single"):
            for trial in range(1, TRIALS + 1):
                print(f"\ntask {number}, {design}, trial {trial}: {task}")
                print(run(build(design), task, design))


def summarize() -> None:
    """Print each task's runs, tokens and time for each design."""
    if not LOG.exists():
        print("No runs logged yet.")
        return
    rows = [json.loads(line) for line in LOG.read_text().splitlines() if line]
    print(
        f"{'design':7} {'runs':>4} {'tokens':>8} {'seconds':>8} "
        f"{'stopped':>8}  task"
    )
    for task in dict.fromkeys(row["task"] for row in rows):
        for design in ("team", "single"):
            mine = [
                r for r in rows if r["task"] == task and r["design"] == design
            ]
            if not mine:
                continue
            tokens = sum(r["input_tokens"] + r["output_tokens"] for r in mine)
            seconds = sum(r["seconds"] for r in mine)
            stopped = sum(1 for r in mine if r["error"])
            print(
                f"{design:7} {len(mine):>4} {tokens // len(mine):>8} "
                f"{seconds / len(mine):>8.1f} {stopped:>8}  {task[:50]}"
            )


def main() -> None:
    """Read the command and do it."""
    if len(sys.argv) >= 3 and sys.argv[1] in ("team", "single"):
        print(run(build(sys.argv[1]), " ".join(sys.argv[2:]), sys.argv[1]))
    elif sys.argv[1:] == ["eval"]:
        evaluate()
    elif sys.argv[1:] == ["log"]:
        summarize()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
