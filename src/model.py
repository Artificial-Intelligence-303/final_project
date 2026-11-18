"""The models the agents on your team use. Provided; do not edit.

The default model is glm-5.3-flash on OpenCode Zen, reached with the key in
`.env`. MODEL in `.env`, or the evaluation, changes the default. An agent
can also be fixed to one model, as `model=model("qwen3.8-max")`, so a team
can mix a cheap model for some agents with a stronger one for others.
`.env` may also set API_URL to use another endpoint that speaks OpenAI chat
completions, such as a local Ollama server.

Each model counts the tokens it uses, so `run` can log the tokens and the
cost of a run for each model.
"""

import os
from pathlib import Path

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

URL = "https://opencode.ai/inference/openai/v1"
NAME = "glm-5.3-flash"

# Dollars per million tokens, input then output, on OpenCode Zen.
PRICES = {
    "glm-5.3-flash": (0.15, 0.50),
    "deepseek-v4.1-flash": (0.30, 1.20),
    "minimax-m3": (0.30, 1.20),
    "glm-5.3": (1.40, 4.40),
    "qwen3.8-max": (2.00, 6.00),
}

# Input and output tokens used by each model since the last reset.
usage_by_model: dict[str, list[int]] = {}
ENV_FILE = Path(__file__).parent.parent / ".env"

# The SDK sends a trace of each run to OpenAI unless this is turned off.
set_tracing_disabled(True)


def setting(name: str) -> str:
    """Read a setting from the environment or from a line in `.env`."""
    value = os.environ.get(name, "")
    if not value and ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith(f"{name}="):
                value = line.split("=", 1)[1].strip().strip("\"'")
    return value


def model_name() -> str:
    """The model in use: MODEL in `.env` if set, otherwise glm-5.3-flash."""
    return setting("MODEL") or NAME


class CountedModel(OpenAIChatCompletionsModel):
    """The SDK's chat completions model, counting the tokens it uses."""

    async def get_response(self, *args, **kwargs):
        """Get the model's reply and add its tokens to usage_by_model."""
        response = await super().get_response(*args, **kwargs)
        counts = usage_by_model.setdefault(str(self.model), [0, 0])
        counts[0] += response.usage.input_tokens
        counts[1] += response.usage.output_tokens
        return response


def cost(counts: dict[str, list[int]]) -> float | None:
    """Dollars for the tokens in `counts`, or None for a model not priced."""
    total = 0.0
    for name, (tokens_in, tokens_out) in counts.items():
        if name not in PRICES:
            return None
        price_in, price_out = PRICES[name]
        total += (tokens_in * price_in + tokens_out * price_out) / 1_000_000
    return total


def model(name: str = "") -> OpenAIChatCompletionsModel:
    """Return the model to give an Agent, as `model=model()`.

    Args:
        name: a model to fix this agent to, such as "glm-5.3-flash". Leave
            it out to use the default: MODEL in `.env`, or the model the
            evaluation is running.
    """
    key = setting("API_KEY") or setting("ZEN_API_KEY") or "no-key-set"
    # A request that gets no answer in 120 seconds is tried again, twice.
    client = AsyncOpenAI(
        base_url=setting("API_URL") or URL,
        api_key=key,
        timeout=120,
        max_retries=2,
    )
    return CountedModel(model=name or model_name(), openai_client=client)
