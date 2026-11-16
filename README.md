# Final Capstone: A Team of Agents

|                     |                                             |
| :------------------ | :------------------------------------------ |
| `Thursday 19 Nov`   | Released, in class                          |
| `Tuesday 24 Nov`    | Plan due, 11:59pm                           |
| `Tuesday 1 Dec`     | Plan sign-off, in lab                       |
| `Tuesday 8 Dec`     | Due 9:00am; presentation and code review    |
| Points              | 16                                          |
| Format              | Individual, or a team of two                |

In Challenge 7 and Project 2, Copilot's agent ran the loop and you supplied
the tools. Here you build the agents yourself, with the OpenAI Agents SDK:
a team of agents with separate roles that works on one task for a person.
Then you test the claim that a team is worth it, by running the same tasks
with one agent that has the same tools and comparing the two.

## What you build

A team for a real task, one a person actually does. You may build on your
Project 2 task, data and tool code. Your team needs all of these, in
`src/team.py`:

1. Three or more agents, each with its own name and a written role in its
   instructions: what it does, and what it leaves to the others.
2. A lead agent that reaches the others through handoffs, through agent
   tools made with `agent.as_tool(...)`, or both. One agent's job is to
   check another's work.
3. Two or more tools of your own, each a function with `@tool` (from
   `run`), type hints and a docstring the model can act on.
4. Guardrails:
   - A tool that changes something calls `ask_person` before it acts, and
     leaves things as they were if the person declines.
   - Two or more checks in your tools that reject a bad call by raising
     `ValueError` with a message the model can act on.
   - The step limit in `run`, which is provided.
5. `build_single()`: one agent with the same tools as the team and no other
   agents, for the comparison.
6. Tests of your own, in at least one file in `tests/`, covering each tool
   and at least one guardrail. Your tests call your tool functions
   directly, so they make no model calls.

If you work as a team of two, your team has four or more agents and your
evaluation has eight tasks. Each of you is graded on your own commits and
on your own answers at the code review.

You may have an AI agent write any of this code. Review each line before
you commit it, because at the code review you will explain any part you
are asked about.

## What is provided

- `src/example_rooms.py`: a finished team that books study rooms. A desk
  agent calls a finder and a checker as tools, then hands the student to a
  booker, whose tool asks the person before booking. Read it first, and run
  it with `uv run python src/example_rooms.py team "Book me a room
  Wednesday"`. It keeps its own log, so it does not count toward your
  checks.
- `src/team.py`: where your team goes.
- `src/model.py`: the model, `glm-5.3-flash` on OpenCode Zen, with your key
  from `.env`. Give each agent `model=model()`.
- `src/run.py`: `run`, which gives a task to an agent with a step limit and
  logs the run in `logs/runs.jsonl`; `ask_person`; and `tool`, which makes
  a function a tool and passes a `ValueError`'s message to the model.
- `src/main.py`: run one task, run your evaluation, or summarize the log.
- `tests/test_team.py` and `tests/test_session.py`: checks on your team and
  on your evaluation log. They must pass, and you do not edit them.
- `docs/plan.md`, `docs/tasks.txt`, `docs/evaluation.md` and
  `docs/reflection.md`, for you to fill in.

## Getting started

1. Copy `.env` from your Challenge 8 folder to the top of this repository.
   It holds one line, `ZEN_API_KEY=` followed by your key, and git leaves
   it out of your commits.
2. Run the example, once as a team and once as a single agent, and read
   both runs in `logs/example-runs.jsonl`.
3. Write your plan.

## Running your team

```bash
uv run python src/main.py team "a request, as the person would type it"
uv run python src/main.py single "the same request"
uv run python src/main.py eval      # each task in docs/tasks.txt, 3 runs each way
uv run python src/main.py log       # runs, average tokens and seconds per task
```

Each line of `logs/runs.jsonl` records one run: which agents acted, each
tool call and its result, each handoff, each approval, the tokens used and
the time taken. The example team used about 3,000 tokens a run, so an
evaluation of six tasks costs a few cents.

## Evaluation

List six tasks in `docs/tasks.txt`, one per line, as the person would type
them. Between them, the tasks include one where you decline a change when
`ask_person` asks, and one where a guardrail rejects a call. Then run
`uv run python src/main.py eval`, which runs each task three times with
your team and three times with your single agent, and answer each approval
as the task calls for. A call rejected inside an agent tool shows up in
that agent's answer rather than as a result in the log, so your single
agent's runs are where the checks find it. Judge each run in `docs/evaluation.md` by the test
you set in your plan, and commit `logs/runs.jsonl`. To start a fresh log
for a clean run, delete the file before you begin.

## The automated checks

Run the checks yourself with `uv run gatorgrade --config gatorgrade.yml`.
They also run on GitHub when you push, and they confirm that your team and
single agent are built as required, that your tests pass, that the log
holds your evaluation with a declined change and a rejected call, that the
style follows the Google Python style guide (`uv run ruff check src
tests`), and that the documents are complete. The repository needs at least
15 commits by the due date.

## What is due, and when

- **Tuesday 24 November, by 11:59pm:** `docs/plan.md`. The instructor reads
  it and posts a Plan sign-off issue, a checklist in which anything left
  unticked is what to change before you build that part. Questions about it
  can be settled in lab on Tuesday 1 December.
- **Tuesday 8 December, 9:00am**, the final exam period: the finished
  project, then your presentation: the task and the team, a live run, and
  your evaluation table. The code review follows, recorded in the Code
  review issue.

## Evaluation of your work

This project is worth 16 points.

| Component | Value |
| :-------- | ----: |
| Implementation | 7 |
| Evaluation of the team against one agent | 3 |
| Presentation | 2 |
| Written reflection | 2 |
| Oral component of the code review | 2 |

## How this project was built

I chose the project's design: a team built with an agent SDK and compared
against a single agent. Claude wrote the provided code, the example team,
the tests and the checks, ran the example on the real model, and drafted
this README, which I reviewed.

## AI use on this project

The full policy is [AI in this course](https://areweagentsyet.com/ai/). The
evaluation runs are the assignment itself. Any other AI use, including an
agent writing your code, is allowed and disclosed in `docs/reflection.md`.
