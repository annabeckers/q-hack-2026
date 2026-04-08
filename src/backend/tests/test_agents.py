"""Agent endpoint tests -- invoke, SSE, validation."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


@patch("app.api.v1.endpoints.agents.invoke_agent", new_callable=AsyncMock, return_value="mock response")
async def test_invoke_returns_response(mock_invoke, client: AsyncClient):
    response = await client.post(
        "/api/v1/agents/invoke",
        json={"prompt": "hello", "framework": "anthropic"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "framework" in data
    assert data["framework"] == "anthropic"


async def test_invoke_invalid_framework_returns_422(client: AsyncClient):
    response = await client.post(
        "/api/v1/agents/invoke",
        json={"prompt": "hello", "framework": "nonexistent"},
    )
    assert response.status_code == 422


@patch("app.api.v1.endpoints.stream.invoke_agent", new_callable=AsyncMock, return_value="streamed")
async def test_sse_returns_event_stream_content_type(mock_invoke, client: AsyncClient):
    response = await client.get(
        "/api/v1/agents/sse",
        params={"prompt": "hello", "framework": "anthropic"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
