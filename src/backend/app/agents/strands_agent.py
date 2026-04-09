"""Strands agent — switchable model provider with tool-calling.

Uses Strands SDK Agent class with native model provider support.
Default: GeminiModel (gemini-2.0-flash). Switch to Ollama for local deployment.

Switching models:
  - Gemini:  MODEL_PROVIDER=gemini  GEMINI_MODEL=gemini-2.0-flash
  - Ollama:  MODEL_PROVIDER=ollama  OLLAMA_MODEL=mistral  OLLAMA_HOST=http://localhost:11434
"""

import structlog
from strands import Agent

from app.agents.strands_tools import ANALYSIS_TOOLS
from app.config import settings

log = structlog.get_logger()

SYSTEM_PROMPT = (
    "You are Argus, an AI security analyst for enterprise AI usage monitoring. "
    "You have tools to query the company's AI usage database — findings about "
    "secrets leaks, PII exposure, slopsquatting, and department-level risk scores. "
    "Use the tools to answer questions with real data. Be concise and actionable. "
    "When presenting data, use structured formats. Always cite specific numbers."
)


def _build_model():
    """Build the appropriate Strands model based on config."""
    provider = settings.model_provider

    if provider == "gemini":
        from strands.models.gemini import GeminiModel

        log.info("strands_model", provider="gemini", model=settings.gemini_model)
        return GeminiModel(
            model_id=settings.gemini_model,
            client_args={"api_key": settings.google_api_key},
            params={"temperature": 0.3},
        )

    elif provider == "ollama":
        from strands.models.ollama import OllamaModel

        log.info("strands_model", provider="ollama", model=settings.ollama_model, host=settings.ollama_host)
        return OllamaModel(
            host=settings.ollama_host,
            model_id=settings.ollama_model,
        )

    elif provider == "openai":
        from strands.models.openai import OpenAIModel

        log.info("strands_model", provider="openai", model=settings.openai_model)
        return OpenAIModel(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            params={"temperature": 0.3},
        )

    else:
        raise ValueError(
            f"Unknown MODEL_PROVIDER: '{provider}'. "
            f"Supported: gemini, ollama, openai"
        )


def create_agent(system_prompt: str = "") -> Agent:
    """Create a Strands Agent with the configured model and analysis tools.

    Args:
        system_prompt: Override the default Argus system prompt.

    Returns:
        Configured Strands Agent ready to invoke.
    """
    model = _build_model()
    return Agent(
        model=model,
        system_prompt=system_prompt or SYSTEM_PROMPT,
        tools=ANALYSIS_TOOLS,
    )


async def run_strands_agent(prompt: str, system: str = "") -> str:
    """Run the Strands agent and return the response text.

    Args:
        prompt: User message.
        system: Optional system prompt override.

    Returns:
        Agent response as string.
    """
    agent = create_agent(system_prompt=system)
    log.info("strands_agent_start", prompt_length=len(prompt))

    # Strands Agent.__call__ is synchronous but handles async tools internally
    result = agent(prompt)

    response_text = str(result)
    log.info("strands_agent_done", response_length=len(response_text))
    return response_text
