"""Anthropic SDK direct agent — tool-calling loop using the anthropic package."""

from app.config import settings


async def run_anthropic_agent(
    prompt: str,
    system: str = "",
    tools: list[dict] | None = None,
    max_turns: int = 10,
) -> str:
    """Run a tool-calling agent loop using Anthropic's API directly.

    Args:
        prompt: User message.
        system: System prompt.
        tools: Tool definitions in Anthropic format.
        max_turns: Max reasoning turns before stopping.

    Returns:
        Final text response.
    """
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    messages = [{"role": "user", "content": prompt}]
    tools = tools or []

    for _ in range(max_turns):
        response = await client.messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=4096,
            system=system or "You are a helpful AI assistant.",
            messages=messages,
            tools=tools if tools else anthropic.NOT_GIVEN,
        )

        # Check if we need to handle tool calls
        if response.stop_reason == "tool_use":
            # Collect tool use blocks
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # TODO: Execute the tool and get result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool {block.name} called with {block.input}",
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            # Final response
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(text_blocks)

    return "Max turns reached"
