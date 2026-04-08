"""Agent API — route requests to selected framework + WebSocket streaming."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.agents.registry import AgentFramework, invoke_agent

router = APIRouter()


class AgentRequest(BaseModel):
    prompt: str
    framework: AgentFramework = AgentFramework.ANTHROPIC
    system: str = ""


class AgentResponse(BaseModel):
    response: str
    framework: str


@router.post("/invoke", response_model=AgentResponse)
async def invoke(body: AgentRequest):
    """Invoke an agent with the selected framework."""
    result = await invoke_agent(
        framework=body.framework,
        prompt=body.prompt,
        system=body.system,
    )
    return AgentResponse(response=result, framework=body.framework.value)


@router.websocket("/stream")
async def agent_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming agent responses.

    Client sends: {"prompt": "...", "framework": "anthropic", "system": "..."}
    Server sends: {"agent": "...", "content": "...", "type": "thinking|response|tool_call|done"}
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            prompt = msg.get("prompt", "")
            framework = AgentFramework(msg.get("framework", "anthropic"))
            system = msg.get("system", "")

            # Send thinking indicator
            await websocket.send_json({
                "agent": framework.value,
                "content": "Processing...",
                "type": "thinking",
            })

            try:
                result = await invoke_agent(framework, prompt, system)
                await websocket.send_json({
                    "agent": framework.value,
                    "content": result,
                    "type": "response",
                })
            except Exception as e:
                await websocket.send_json({
                    "agent": framework.value,
                    "content": str(e),
                    "type": "error",
                })

            await websocket.send_json({
                "agent": framework.value,
                "content": "",
                "type": "done",
            })

    except WebSocketDisconnect:
        pass
