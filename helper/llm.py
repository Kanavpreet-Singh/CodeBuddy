import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"
OPENAI_MODEL = "openai/gpt-4o-mini"

# Registry of selectable models. Order matters: the first available one is the
# default shown in the UI. OpenAI (gpt-4o-mini) is preferred because its
# tool-calling / structured output is more reliable than Groq's gpt-oss.
_MODELS = {
    "openai": {"label": "OpenAI · gpt-4o-mini", "env": "OPENAI_API_KEY"},
    "groq": {"label": "Groq · gpt-oss-120b", "env": "GROQ_API_KEY"},
}


def available_models() -> list[dict]:
    """Models whose API keys are configured, in preference order."""
    return [
        {"id": mid, "label": m["label"]}
        for mid, m in _MODELS.items()
        if os.environ.get(m["env"])
    ]


def default_model_id() -> str:
    models = available_models()
    return models[0]["id"] if models else "groq"


def make_llm(model_id: str | None = None, temperature: float = 0.0):
    """Builds a chat model for the given model id at the given temperature."""
    model_id = model_id or default_model_id()

    if model_id == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_BASE_URL", "https://aicredits.in/v1"),
            temperature=temperature,
        )

    # default: Groq
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=os.environ["GROQ_API_KEY"],
        temperature=temperature,
        reasoning_effort="low",
    )


# Backwards-compatible default instance.
llm = make_llm()

# gpt-4o-mini public rates (USD per 1M tokens). The AICredits proxy may price
# differently, so treat this as an estimate, not a bill.
_OPENAI_RATES_USD_PER_M = {"input": 0.15, "output": 0.60}
_USD_TO_INR = 85.0


def estimate_cost_inr(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Rough INR cost estimate for a run. Groq (free tier) is treated as 0."""
    if model_id != "openai":
        return 0.0
    usd = (
        input_tokens / 1_000_000 * _OPENAI_RATES_USD_PER_M["input"]
        + output_tokens / 1_000_000 * _OPENAI_RATES_USD_PER_M["output"]
    )
    return round(usd * _USD_TO_INR, 4)
