"""Agent registry — dynamic framework selection at runtime.

Allows switching between agent frameworks (Strands, LangGraph, OpenAI, Anthropic, A2A)
based on configuration or request parameters.
"""

from enum import Enum


class AgentFramework(str, Enum):
    STRANDS = "strands"
    LANGGRAPH = "langgraph"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    A2A = "a2a"


async def invoke_agent(framework: AgentFramework, prompt: str, system: str = "") -> str:
    """Invoke an agent using the specified framework.

    Args:
        framework: Which agent framework to use.
        prompt: User message.
        system: System prompt / instructions.

    Returns:
        Agent response text.
    """
    if framework == AgentFramework.STRANDS:
        from app.agents.strands_agent import create_strands_agent, make_strands_tools

        agent = create_strands_agent(system_prompt=system, tools=make_strands_tools())
        result = agent(prompt)
        return str(result)

    elif framework == AgentFramework.LANGGRAPH:
        from app.agents.langgraph_agent import build_agent_graph

        graph = build_agent_graph()
        result = graph.invoke({"messages": [prompt], "context": system})
        return str(result["messages"][-1])

    elif framework == AgentFramework.OPENAI:
        from app.agents.openai_agent import create_openai_agent, run_openai_agent

        agent = create_openai_agent(instructions=system)
        return await run_openai_agent(agent, prompt)

    elif framework == AgentFramework.ANTHROPIC:
        from app.agents.anthropic_agent import run_anthropic_agent

        return await run_anthropic_agent(prompt=prompt, system=system)

    elif framework == AgentFramework.A2A:
        from app.agents.a2a_agent import handle_a2a_task

        result = await handle_a2a_task({
            "id": "local",
            "message": {"parts": [{"type": "text", "text": prompt}]},
        })
        artifacts = result.get("artifacts", [])
        if artifacts:
            parts = artifacts[0].get("parts", [])
            return " ".join(p["text"] for p in parts if p.get("type") == "text")
        return ""

    else:
        raise ValueError(f"Unknown framework: {framework}")
