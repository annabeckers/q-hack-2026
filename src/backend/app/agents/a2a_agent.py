"""Google A2A (Agent-to-Agent) SDK skeleton.

A2A enables inter-agent communication using Google's protocol.
This skeleton sets up an A2A-compatible agent that can be discovered
and communicated with by other agents.

Note: A2A is a protocol spec — the agent logic itself uses any LLM.
The SDK handles agent discovery, task routing, and message passing.
"""


class A2AAgentCard:
    """Agent card for A2A discovery — describes this agent's capabilities."""

    def __init__(self, name: str = "hackathon-agent", description: str = ""):
        self.card = {
            "name": name,
            "description": description or "A hackathon AI agent",
            "url": "http://localhost:8000/api/v1/agents/a2a",
            "version": "0.1.0",
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
            },
            "skills": [
                {
                    "id": "general",
                    "name": "General Assistant",
                    "description": "General-purpose AI assistant with tool access",
                }
            ],
        }

    def to_dict(self) -> dict:
        return self.card


async def handle_a2a_task(task: dict) -> dict:
    """Handle an incoming A2A task.

    The A2A protocol sends tasks as JSON with:
    - id: task ID
    - message: the user/agent message
    - sessionId: optional session for multi-turn

    Args:
        task: A2A task payload.

    Returns:
        A2A task response with artifacts.
    """
    message = task.get("message", {})
    text_parts = [p["text"] for p in message.get("parts", []) if p.get("type") == "text"]
    user_input = " ".join(text_parts)

    # TODO: Route to your LLM of choice and process
    response_text = f"Processed: {user_input}"

    return {
        "id": task["id"],
        "status": {"state": "completed"},
        "artifacts": [
            {
                "parts": [{"type": "text", "text": response_text}],
            }
        ],
    }
