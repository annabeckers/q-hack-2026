"""SSE (Server-Sent Events) endpoint — alternative to WebSocket for agent streaming.

SSE is simpler than WebSocket: one-way server->client, works through proxies/CDNs,
auto-reconnects, and needs no special client library.
"""

import json
import asyncio

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.agents.registry import AgentFramework, invoke_agent

router = APIRouter()


@router.get("/sse")
async def agent_sse(
    prompt: str = Query(..., description="User prompt"),
    framework: AgentFramework = Query(AgentFramework.ANTHROPIC),
    system: str = Query("", description="System prompt"),
):
    """Stream agent responses via Server-Sent Events.

    Usage: EventSource("/api/v1/agents/sse?prompt=hello&framework=anthropic")
    """

    async def event_stream():
        # Send thinking event
        yield f"data: {json.dumps({'agent': framework.value, 'type': 'thinking', 'content': 'Processing...'})}\n\n"

        try:
            result = await invoke_agent(framework, prompt, system)
            yield f"data: {json.dumps({'agent': framework.value, 'type': 'response', 'content': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'agent': framework.value, 'type': 'error', 'content': str(e)})}\n\n"

        yield f"data: {json.dumps({'agent': framework.value, 'type': 'done', 'content': ''})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
