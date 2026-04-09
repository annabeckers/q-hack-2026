"""AWS Strands SDK agent skeleton.

Uses the strands-agents package to create an agent with tool-calling
capabilities via AWS Bedrock.

Pattern from Astrofarm/EDEN project.
"""

from app.config import settings


def create_strands_agent(system_prompt: str = "", tools: list | None = None):
    """Create a Strands Agent instance.

    Args:
        system_prompt: The agent's system prompt.
        tools: List of @tool-decorated functions.

    Returns:
        A strands.Agent instance ready for invocation.
    """
    from strands import Agent
    from strands.models.bedrock import BedrockModel

    model = BedrockModel(
        model_id=settings.aws_bedrock_model_id,
        region_name=settings.aws_region,
    )

    agent = Agent(
        model=model,
        tools=tools or [],
        system_prompt=system_prompt or "You are a helpful AI assistant.",
    )
    return agent


def make_strands_tools() -> list:
    """Create @tool-decorated functions for the Strands agent.

    Returns:
        List of tool-decorated callables for Agent(tools=...).
    """
    from strands.tools import tool

    @tool
    def search_knowledge(query: str) -> str:
        """Search the knowledge base for relevant information.

        Args:
            query: The search query string.
        """
        # TODO: Implement with database search
        return f"Knowledge base results for: {query}"

    @tool
    def query_graph_db(cypher: str) -> str:
        """Execute a Cypher query against Neo4j.

        Args:
            cypher: The Cypher query to execute.
        """
        # TODO: Implement with Neo4j driver
        return f"Graph results for: {cypher}"

    return [search_knowledge, query_graph_db]
