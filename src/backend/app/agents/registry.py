"""Agent registry — dynamic framework selection at runtime.

Routes agent invocations to the configured framework. Default is Strands SDK
with Gemini model, which supports easy switching to Ollama/OpenAI via config.
"""

from enum import Enum


class AgentFramework(str, Enum):
    GEMINI = "gemini"
    STRANDS = "strands"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


async def invoke_agent(framework: AgentFramework, prompt: str, system: str = "") -> str:
    """Invoke an agent using the specified framework.

    Args:
        framework: Which agent framework to use.
        prompt: User message.
        system: System prompt / instructions.

    Returns:
        Agent response text.
    """
    # Both "gemini" and "strands" route to the Strands SDK agent
    # (Strands handles the model provider internally based on MODEL_PROVIDER env var)
    if framework in (AgentFramework.GEMINI, AgentFramework.STRANDS):
        from app.agents.strands_agent import run_strands_agent

        return await run_strands_agent(prompt=prompt, system=system)

    elif framework == AgentFramework.OPENAI:
        from app.agents.strands_agent import run_strands_agent

        # OpenAI also goes through Strands — just override the provider
        return await run_strands_agent(prompt=prompt, system=system)

    elif framework == AgentFramework.ANTHROPIC:
        from app.agents.strands_agent import run_strands_agent

        return await run_strands_agent(prompt=prompt, system=system)

    else:
        raise ValueError(f"Unknown framework: {framework}")
