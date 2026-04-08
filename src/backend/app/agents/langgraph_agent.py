"""LangGraph agent skeleton.

Uses StateGraph pattern from LangGraph to define an agent workflow
with tool-calling capabilities.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State passed between nodes in the agent graph."""
    messages: Annotated[list, add_messages]
    context: str


def agent_node(state: AgentState) -> AgentState:
    """Main agent reasoning node.

    TODO: Replace with actual LLM call using langchain_core ChatModel.
    """
    messages = state["messages"]
    last_message = messages[-1] if messages else ""
    return {
        "messages": [f"Agent processed: {last_message}"],
        "context": state.get("context", ""),
    }


def tool_node(state: AgentState) -> AgentState:
    """Tool execution node.

    TODO: Integrate with tools from app.agents.tools
    """
    return state


def should_use_tools(state: AgentState) -> str:
    """Route to tools or end based on agent response."""
    # TODO: Check if agent response contains tool calls
    return "end"


def build_agent_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_use_tools, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")

    return graph.compile()
