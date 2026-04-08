"""OpenAI Agent SDK skeleton.

Uses the openai-agents package for building agents with tool-calling.
"""

from app.config import settings


def create_openai_agent(instructions: str = "", tools: list | None = None):
    """Create an OpenAI Agent instance.

    Args:
        instructions: The agent's system instructions.
        tools: List of tool functions.

    Returns:
        An agents.Agent instance.
    """
    from agents import Agent, OpenAIChatCompletionsModel
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    model = OpenAIChatCompletionsModel(model="gpt-4o", openai_client=client)

    agent = Agent(
        name="hackathon-agent",
        instructions=instructions or "You are a helpful AI assistant.",
        model=model,
        tools=tools or [],
    )
    return agent


async def run_openai_agent(agent, prompt: str) -> str:
    """Run the agent and return the final response."""
    from agents import Runner

    result = await Runner.run(agent, prompt)
    return result.final_output
