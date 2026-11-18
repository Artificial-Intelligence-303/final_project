# Final Capstone: A Team of Agents

|                     |                                             |
| :------------------ | :------------------------------------------ |
| `Thursday 19 Nov`   | Released, in class                          |
| `Tuesday 24 Nov`    | Plan due, 11:59pm                           |
| `Tuesday 1 Dec`     | Plan sign-off, in lab                       |
| `Tuesday 8 Dec`     | Due 9am; presentation and code review       |
| Points              | 16                                          |
| Format              | Individual, or a team of two                |

In Challenge 7 and Project 2, Copilot's agent ran the loop and you supplied
the tools. Here you build the agents yourself, with the OpenAI Agents SDK:
a team of agents with separate roles that works on one task for a person.
Then you test the claim that a team is worth it, by running the same tasks
with one agent that has the same tools and comparing the two.

## How the pieces fit

### The SDK

The OpenAI Agents SDK is the Python package `openai-agents`, imported as
`agents`. `uv sync` installs it. It gives you three things this project
uses:

- `Agent`, a class. An agent is an instance of it, and a second agent
  is a second instance:

  ```python
  from agents import Agent

  finder = Agent(
      name="Finder",
      instructions="You find free study rooms. ...",
      tools=[free_rooms],
      model=model(),
  )
  ```

  `name` is how the log and the other agents refer to it. `instructions`
  is its role, which the model reads at the start of each turn. `tools`
  lists the functions it may call. `handoffs` lists the agents it may pass
  the conversation to. `model` is the model it runs on.
- `agent.as_tool(name, description)`, which turns an agent into a tool
  that another agent can call. The calling agent sends it a request, the
  agent works on it with its own tools, and its final answer comes back as
  the tool's result. The caller stays in charge.
- `Runner`, which runs the loop: send the conversation to the model,
  carry out the tool call or handoff the model asks for, add the result to
  the conversation, and repeat until the model answers in plain text. You
  do not call `Runner` yourself; `run` in `src/run.py` calls it for you.

A handoff passes the conversation to another agent, which carries on
from there and gives the final answer. The SDK offers each handoff to the
model as a tool named `transfer_to_` and the agent's name.

The SDK works with any model behind an OpenAI chat completions endpoint,
which is how it runs here on OpenCode Zen.

### The files

| File | Yours or provided | What it holds |
| :--- | :--- | :--- |
| `src/team.py` | yours | your tools, your agents, `build_team()` and `build_single()` |
| `tests/test_*.py` of your own | yours | tests of your tools that call them directly, with no model calls |
| `docs/plan.md`, `docs/tasks.txt`, `docs/evaluation.md`, `docs/reflection.md` | yours | the plan, the six tasks, the comparison, the reflection |
| `src/example_rooms.py` | provided, to read | a finished team that books study rooms, in the shape your `team.py` takes |
| `src/model.py` | provided | `model()`, which returns the model to give each agent, using your key in `.env` |
| `src/run.py` | provided | `tool`, `ask_person` and `run`, described below |
| `src/main.py` | provided | the commands that run one task, run the evaluation, and summarize the log |
| `tests/test_team.py`, `tests/test_session.py` | provided, do not edit | checks on how your team is built and on your evaluation log |

`src/run.py` holds the three functions you use from your own code:

- `@tool` above a function makes it a tool. The model reads the
  function's name, type hints and docstring to decide when to call it and
  with what. If the function raises `ValueError`, the message goes back to
  the model as the result, starting `error:`, so the model can try again.
  The plain function stays reachable as `.function`, which is how your
  tests call it: `free_rooms.function("Wednesday")`.
- `ask_person(question)` asks the person at the keyboard to approve a
  change and returns `True` or `False`. Call it inside any tool that
  changes something, before it acts.
- `run(lead, task, design)` gives a task to the lead agent, stops it
  after 15 steps, writes one line to `logs/runs.jsonl`, and returns the
  final answer. `main.py` calls it for you.

### What happens on a run

`uv run python src/main.py team "a request"` does this:

1. `main.py` calls your `build_team()`, which creates the agents and
   returns the lead.
2. `main.py` passes the lead and the request to `run`.
3. `run` hands both to the SDK's `Runner`, which starts the loop with the
   lead agent.
4. On each turn, the model reads the active agent's instructions, the
   conversation so far, and its tools, then either calls a tool, calls an
   agent tool, hands off, or answers.
5. When the model answers in plain text, the loop ends, and `run` writes
   the log line and returns the answer.

This is a real run of the example team, started with `uv run python
src/example_rooms.py team "Book me a room Wednesday afternoon, after 2:30"`,
shortened from its log line:

```text
Desk     agent call  find_rooms     "Find free study room slots on Wednesday afternoon, after 2:30"
Desk     result                     "... free study room slots on Wednesday after 2:30 PM: Room C at 3pm"
Desk     agent call  check_booking  "Check proposed booking: Room C on Wednesday at 3:00 PM ..."
Desk     result                     "... Room C is listed as free on Wednesday at 3:00 PM ... The booking can proceed."
Desk     handoff     Booker
Booker   tool call   book           {"day": "Wednesday", "slot": "Room C at 3pm"}
                                    Book Room C at 3pm on Wednesday? Approve? [y/n] y
Booker   result                     "booked Room C at 3pm on Wednesday"
Booker   message                    "Your booking is confirmed: Room C, Wednesday at 3:00 PM. ..."
```

The finder and the checker each ran their own loop inside a call from the
desk. The booker took over after the handoff and gave the final answer.
The run used about 3,500 tokens and took 12 seconds.

`single` does the same with `build_single()`: one agent, the same tools, no
agent tools and no handoffs.

## What you build

A team for a real task, one a person actually does. You may build on your
Project 2 task, data and tool code. All of it goes in `src/team.py`:

1. Two or more tools of your own, each a function with `@tool`, type
   hints, and a docstring the model can act on.
2. Three or more agents, each an `Agent(...)` with its own name and a
   role in its instructions: what it does, and what it leaves to the
   others. One agent's job is to check another's work.
3. A lead agent that reaches the others through handoffs, through agent
   tools made with `agent.as_tool(...)`, or both. `build_team()` returns
   it.
4. Guardrails:
   - A tool that changes something calls `ask_person` before it acts, and
     leaves things as they were if the person declines.
   - Two or more checks in your tools that reject a bad call by raising
     `ValueError` with a message the model can act on.
   - The step limit in `run`, which is provided.
5. `build_single()`, which returns one agent with the same tools as the
   team and no other agents, for the comparison.
6. Tests of your own, in at least one file in `tests/`, covering each
   tool and at least one guardrail. Your tests call each tool's plain
   function, such as `free_rooms.function("Wednesday")`, so they make no
   model calls.

If you work as a team of two, your team has four or more agents and your
evaluation has eight tasks. Each of you is graded on your own commits and
on your own answers at the code review.

You may have an AI agent write any of this code. Review each line before
you commit it, because at the code review you will explain any part you
are asked about.

## Getting started

1. Accept the assignment, clone your repository, and run `uv sync`.
2. Copy `.env` from your Challenge 8 folder to the top of this repository.
   It holds one line, `ZEN_API_KEY=` followed by your key, and git leaves
   it out of your commits.
3. Run the example as a team and as a single agent, and approve or decline
   when it asks:

   ```bash
   uv run python src/example_rooms.py team "Book me a room Wednesday"
   uv run python src/example_rooms.py single "Book me a room Wednesday"
   ```

   Open `logs/example-runs.jsonl` and find each step of the two runs.
4. Read `src/example_rooms.py` from top to bottom. Your `team.py` follows
   its shape.
5. Write `docs/plan.md`, due Tuesday 24 November.

Once your plan is signed off, build in this order, running the checks as
you go:

1. Write your tools and their tests, in a file such as
   `tests/test_tools.py`. `uv run pytest tests/test_tools.py` runs them
   without the model.
2. Write `build_single()` and try it with `uv run python src/main.py single
   "..."`.
3. Add the agents one at a time, with `build_team()` returning the lead,
   and try each with `uv run python src/main.py team "..."`. Read the log
   line to see which agents acted.
4. Write your six tasks in `docs/tasks.txt`, then run the evaluation on
   your three models.
5. Write `docs/evaluation.md`, then `docs/reflection.md`.

## Running your team

```bash
uv run python src/main.py team "a request, as the person would type it"
uv run python src/main.py single "the same request"
uv run python src/main.py eval glm-5.3-flash   # each task, 3 runs each way, on that model
uv run python src/main.py log                  # runs, average tokens and seconds, by model and task
```

`team` and `single` run on `glm-5.3-flash` unless `.env` names another
model with a line such as `MODEL=kimi-k2.6`. Each line of `logs/runs.jsonl`
records one run: the model, which agents acted, each tool call and its
result, each handoff, each approval, the tokens used and the time taken.

## Choosing three models

Your key reaches five models on OpenCode Zen. Choose three of them for
your evaluation, and say why in your plan.

| Model | Input, per million tokens | Output, per million tokens |
| :---- | ----: | ----: |
| `glm-5.3-flash` | $0.15 | $0.50 |
| `deepseek-v4.1-flash` | $0.30 | $1.20 |
| `minimax-m3` | $0.30 | $1.20 |
| `kimi-k2.6` | $0.95 | $4.00 |
| `qwen3.8-max` | $2.00 | $6.00 |

Your key has a monthly budget, so build and test on `glm-5.3-flash`, the
cheapest, and use the others for the evaluation.

## Evaluation

List six tasks in `docs/tasks.txt`, one per line, as the person would type
them. Between them, the tasks include one where you decline a change when
`ask_person` asks, and one where a guardrail rejects a call. End each line
that leads to a change with `| approve` or `| decline`, and the evaluation
gives that answer when the team asks:

```text
Book me the 3pm room on Wednesday. | approve
Book me a room on Wednesday afternoon. | decline
```

Then run the evaluation on each of your three models, one at a time or
together:

```bash
uv run python src/main.py eval glm-5.3-flash kimi-k2.6 deepseek-v4.1-flash
```

On each model, it runs each task three times with your team and three
times with your single agent. A call rejected inside an agent tool shows up
in that agent's answer rather than as a result in the log, so your single
agent's runs are where the checks find it. Judge each run in
`docs/evaluation.md` by the test you set in your plan, and commit
`logs/runs.jsonl`. To start a fresh log for a clean run, delete the file
before you begin.

## The automated checks

Run the checks yourself with `uv run gatorgrade --config gatorgrade.yml`.
They also run on GitHub when you push, and they confirm that your team and
single agent are built as required, that your tests pass, that the log
holds your evaluation on three models with a declined change and a
rejected call, that the
style follows the Google Python style guide (`uv run ruff check src
tests`), and that the documents are complete. The repository needs at least
15 commits by the due date.

## What is due, and when

- **Tuesday 24 November, by 11:59pm:** `docs/plan.md`. The instructor reads
  it and posts a Plan sign-off issue, a checklist in which anything left
  unticked is what to change before you build that part. Questions about it
  can be settled in lab on Tuesday 1 December.
- **Tuesday 8 December, 9am**, the final exam period: the finished
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
