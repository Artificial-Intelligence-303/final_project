# Final Project: A Team of Agents

|                     |                                             |
| :------------------ | :------------------------------------------ |
| `Thursday 19 Nov`   | Released, in class                          |
| `Tuesday 24 Nov`    | Plan due, 11:59pm                           |
| `Tuesday 1 Dec`     | Plan sign-off, in lab                       |
| `Tuesday 8 Dec`     | Due 9am; presentation and questions         |
| Points              | 19                                          |
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

  reader = Agent(
      name="Reader",
      instructions="You read one batch of support messages ...",
      tools=[read_tickets],
      model=model("glm-5.3-flash"),
  )
  ```

  `name` is how the log and the other agents refer to it. `instructions`
  is its role, which the model reads at the start of each turn. `tools`
  lists the functions it may call. `handoffs` lists the agents it may pass
  the conversation to. `model` is the model it runs on: `model()` for the
  default, or `model("glm-5.3-flash")` to fix this agent to one model.
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
| `src/example_inbox.py`, `example_data/` | provided, to read | a finished team that sorts a support inbox, in the shape your `team.py` takes |
| `src/model.py` | provided | `model()`, which returns the model to give each agent, using your key in `.env`, and counts each model's tokens |
| `src/run.py` | provided | `tool`, `ask_person` and `run`, described below |
| `src/main.py` | provided | the commands that run one task, run the evaluation, and summarize the log |
| `tests/test_team.py`, `tests/test_session.py` | provided, do not edit | checks on how your team is built and on your evaluation log |

`src/run.py` holds the three functions you use from your own code:

- `@tool` above a function makes it a tool. The model reads the
  function's name, type hints and docstring to decide when to call it and
  with what. If the function raises `ValueError`, the message goes back to
  the model as the result, starting `error:`, so the model can try again.
  The plain function stays reachable as `.function`, which is how your
  tests call it: `read_tickets.function(1, 3)`.
- `ask_person(question)` asks the person at the keyboard to approve a
  change and returns `True` or `False`. Call it inside any tool that
  changes something, before it acts.
- `run(lead, task, design)` gives a task to the lead agent, stops it
  after 15 steps, writes one line to `logs/runs.jsonl` with the tokens and
  the cost of each model, and returns the final answer. `main.py` calls it
  for you.

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

The example team has three agents. The lead splits the inbox into six
batches of 50 messages and calls the reader once for each batch. The
reader, fixed to `glm-5.3-flash`, sorts its batch and returns counts, and
the lead adds them up. A checker confirms a bug before the lead files it.
This is a real run, with the lead on `qwen3.8-max`, shortened from its log
line:

```text
Lead   tool call   count_tickets  {}
Lead   result                     "300 messages, numbered 1 to 300"
Lead   agent call  read_batch     "Read messages 1 to 50. Count how many fall into each category ..."
Lead   agent call  read_batch     "Read messages 51 to 100. ..."
   ... four more read_batch calls, in the same turn ...
Lead   result                     "login: 7 (#4, #10, #11, ...) android crash: 8 (#3, #23, ...) ..."
   ... five more results, one per batch ...
Lead   message                    "Top three problems: login 41, missing order 37, payment 34 ..."
```

The six reader calls came in one turn, so the SDK ran them at the same
time, each in its own fresh conversation. The lead did not read any message itself.
The run took 36 seconds and cost 3.2 cents: `qwen3.8-max` used about 7,300
tokens and `glm-5.3-flash` about 27,000. One `qwen3.8-max` agent doing the
same task alone read each message itself, took over three minutes, and
cost about 20 cents.

`single` does the same with `build_single()`: one agent, the same tools, no
agent tools and no handoffs.

## What you build

A team for a real task, one a person actually does. You may build on your
Project 2 task, data and tool code. Your task cannot be the example's, a
support or feedback inbox. All of it goes in `src/team.py`:

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
   function, such as `read_tickets.function(1, 3)`, so they make no
   model calls.

If you work as a team of two, your team has four or more agents and your
evaluation has eight tasks. Each of you is graded on your own commits and
on your own answers to questions after the presentation.

You may have an AI agent write any of this code. Review each line before
you commit it, because in the questions after your presentation you will
explain any part you are asked about.

## Choosing a task a team is good at

A team costs more than one agent, because each agent reads its own
instructions and passing work between agents takes extra model calls. It
pays off when at least one of these is true of your task, and your plan
says which:

- There is more to read than one conversation handles well, such as
  hundreds of messages, reviews or records. Workers each read a part in a
  fresh conversation and return a short summary, so the lead does not hold
  the raw text.
- Parts of the work are independent. The lead calls several workers in the
  same turn, and the SDK runs them at the same time, so the team finishes
  sooner.
- Different parts need different models. Reading and sorting can run on a
  cheap model while the agent that decides runs on a stronger one. Fix an
  agent to a model with `model=model("glm-5.3-flash")`.
- A second look catches mistakes. A checker that reads the evidence in its
  own conversation, without the reasoning behind a proposal, catches what
  the proposer talked itself into.
- Some text should not reach the agents that act. Agents that read text
  from strangers get no tools that change anything.

A Project 2 task with a small data set usually fits in one conversation,
and one agent does as well there. If you build on it, give the team more to
work with, such as a semester of records instead of a week.

Tasks that fit:

- Reviews of several products or places: compare them one by one, then
  recommend.
- Forty paper abstracts: sort them by topic and choose what to read first.
- A season of game statistics: answer questions that need each game.
- A city's open data, such as service requests or inspections: summarize
  by neighborhood and flag patterns worth a closer look.

## Getting started

1. Accept the assignment, clone your repository, and run `uv sync`.
2. Copy `.env` from your Challenge 8 folder to the top of this repository.
   It holds one line, `ZEN_API_KEY=` followed by your key, and git leaves
   it out of your commits.
3. Run the example as a team and as a single agent:

   ```bash
   uv run python src/example_inbox.py team "How many messages report a crash?"
   uv run python src/example_inbox.py single "How many messages report a crash?"
   ```

   Open `logs/example-runs.jsonl` and find each step of the two runs, and
   the tokens each model used.
4. Read `src/example_inbox.py` from top to bottom. Your `team.py` follows
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
   your two models.
5. Write `docs/evaluation.md`, then `docs/reflection.md`.

## Running your team

```bash
uv run python src/main.py team "a request, as the person would type it"
uv run python src/main.py single "the same request"
uv run python src/main.py eval glm-5.3-flash   # each task, 2 runs each way, on that model
uv run python src/main.py log                  # runs, tokens, cents and seconds, by model and task
```

`team` and `single` run on `glm-5.3-flash` unless `.env` names another
model with a line such as `MODEL=minimax-m3`. An agent fixed to a model
with `model("...")` stays on it. Each line of `logs/runs.jsonl`
records one run: the model, which agents acted, each tool call and its
result, each handoff, each approval, the tokens each model used, the cost
in dollars, and the time taken.

## Choosing your second model

Your evaluation runs on two models: `glm-5.3-flash`, the cheapest, and one
more of your choice. Say which in your plan, and which agents on your team
run on which model.

| Model | Input, per million tokens | Output, per million tokens |
| :---- | ----: | ----: |
| `glm-5.3-flash` | $0.15 | $0.50 |
| `deepseek-v4.1-flash` | $0.30 | $1.20 |
| `minimax-m3` | $0.30 | $1.20 |
| `glm-5.3` | $1.40 | $4.40 |
| `qwen3.8-max` | $2.00 | $6.00 |

If a model answers with an error such as 410, it is unavailable for now,
so choose another. Build and test on `glm-5.3-flash`.

## Evaluation

List six tasks in `docs/tasks.txt`, one per line, as the person would type
them. Between them, the tasks include one where you decline a change when
`ask_person` asks, and one where a guardrail rejects a call. End each line
that leads to a change with `| approve` or `| decline`, and the evaluation
gives that answer when the team asks. A line without one declines any
change, so you do not answer approvals by hand during the evaluation:

```text
How many messages report the app crashing on Android?
File a bug for each problem that at least 25 messages report. | approve
File a bug for the wrong dining hall hours. | decline
```

Then run the evaluation on your two models, one at a time or together:

```bash
uv run python src/main.py eval glm-5.3-flash minimax-m3
```

On each model, it runs each task twice with your team and twice with
your single agent, so 24 runs a model. A call rejected inside an agent
tool shows up in that agent's answer rather than as a result in the log,
so your single agent's runs are where the checks find it. Judge each run
in `docs/evaluation.md` by the test you set in your plan, and commit
`logs/runs.jsonl`. To start a fresh log for a clean run, delete the file
before you begin.

### Planning your time and budget

The runs take real time, and your key has a monthly budget, so start the
evaluation early enough to run it twice.

- Time: on the example's tasks, a run took about 25 to 70 seconds on
  `glm-5.3-flash`. On `qwen3.8-max`, a team run took about 45 seconds and
  a single-agent run up to three and a half minutes. Time two of your own
  runs with `main.py team` and `main.py single`, then multiply by 24 for
  each model. Plan for a second evaluation after you fix something, and
  finish your evaluation by Saturday 5 December, so you have time to write
  about it.
- Budget: your key can spend $5 a month, and the December budget starts
  on 1 December. On the example's tasks, a run cost about 1 cent on
  `glm-5.3-flash`. On `qwen3.8-max`, a team run with its readers on
  `glm-5.3-flash` cost about 4 cents and a single-agent run about 20 cents.
  `uv run python src/main.py log` shows the cents per run, so after a few
  runs you can estimate the rest. If your key reaches its budget, the
  evaluation stops and says so.
- Keep your computer awake, since a laptop that sleeps pauses the runs. On a
  Mac, start the evaluation with `caffeinate -i` in front of it, as in
  `caffeinate -i uv run python src/main.py eval glm-5.3-flash minimax-m3`.

## The automated checks

Run the checks yourself with `uv run gatorgrade --config gatorgrade.yml`.
They also run on GitHub when you push, and they confirm that your team and
single agent are built as required, that your tests pass, that the log
holds your evaluation on two models with a declined change and a
rejected call, that the
style follows the Google Python style guide (`uv run ruff check src
tests`), and that the documents are complete. The repository needs at least
15 commits by the due date.

## Your presentation

On Tuesday 8 December, each student or pair presents for five minutes, then
answers about two minutes of questions. A pair presents for seven minutes
and answers questions for three, and each of you answers some questions on
your own. Have your repository open in your editor and your log ready, so
you show your own work rather than slides about it. One slide for the task
and one for your team is enough.

Show these, in this order:

1. The task and the person: who they are, what they need, and one request
   they would type.
2. Your team: each agent, its role, the model it runs on, and how the lead
   reaches it (as a tool or by handoff). Say which reason from "Choosing a
   task a team is good at" made a team worth building.
3. Your code: one tool and its guardrail, and the line where the lead
   reaches another agent. Say what each does.
4. One run, step by step: which agent acted, which tool it called, and what
   came back. Start a live run if it finishes in under a minute; otherwise,
   open a run in `logs/runs.jsonl` and walk through it.
5. Your evaluation: the table for each model, and your answer to "The team
   or the model?"

The questions are about your own work. Expect to be asked to point to a
line in your code and say what it does, to explain a step in your log, or
to say what would change if one agent, tool or model changed. You may have
had an AI agent write your code; you still answer for each line of it.

## What is due, and when

- **Tuesday 24 November, by 11:59pm:** `docs/plan.md`. The instructor reads
  it and posts a Plan sign-off issue, a checklist in which anything left
  unticked is what to change before you build that part. Questions about it
  can be settled on Tuesday 1 December, when class and lab are work time
  for this project.
- **Tuesday 8 December, 9am**, the final exam period: the finished
  project, then your presentation and questions, recorded in the
  Presentation issue.

## Evaluation of your work

This project is worth 19 points.

| Component | Value |
| :-------- | ----: |
| Implementation | 7 |
| Evaluation of the team against one agent | 4 |
| Presentation | 3 |
| Questions about your work | 3 |
| Written reflection | 2 |

## How this project was built

I chose the project's design: a team built with an agent SDK and compared
against a single agent. Claude wrote the provided code, the example team,
the tests and the checks, ran the example on the real model, and drafted
this README, which I reviewed.

## AI use on this project

The full policy is [AI in this course](https://areweagentsyet.com/ai/). The
evaluation runs are the assignment itself. Any other AI use, including an
agent writing your code, is allowed and disclosed in `docs/reflection.md`.
