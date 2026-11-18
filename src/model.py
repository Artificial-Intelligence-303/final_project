"""The model the agents on your team use. Provided; do not edit.

The model is glm-5.3-flash on OpenCode Zen, reached with the key in `.env`.
`.env` may also set API_URL and MODEL to use another endpoint that speaks
OpenAI chat completions, such as a local Ollama server.
"""

import os
from pathlib import Path

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

URL = "https://opencode.ai/inference/openai/v1"
NAME = "glm-5.3-flash"
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


def model() -> OpenAIChatCompletionsModel:
    """Return the model to give each Agent you create, as `model=model()`."""
    key = setting("API_KEY") or setting("ZEN_API_KEY") or "no-key-set"
    # A request that gets no answer in 60 seconds is tried again, twice.
    client = AsyncOpenAI(
        base_url=setting("API_URL") or URL,
        api_key=key,
        timeout=60,
        max_retries=2,
    )
    return OpenAIChatCompletionsModel(model=model_name(), openai_client=client)
