"""Agent endpoint + Strands integration tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


# ── API endpoint tests ────────────────────────────────────────────────────


@patch("app.api.v1.endpoints.agents.invoke_agent", new_callable=AsyncMock, return_value="strands mock response")
async def test_invoke_gemini_framework(mock_invoke, client: AsyncClient):
    """POST /agents/invoke with gemini framework returns a response."""
    response = await client.post(
        "/api/v1/agents/invoke",
        json={"prompt": "What are our top security risks?", "framework": "gemini"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "gemini"
    assert "response" in data
    mock_invoke.assert_called_once()


@patch("app.api.v1.endpoints.agents.invoke_agent", new_callable=AsyncMock, return_value="default response")
async def test_invoke_default_framework_is_gemini(mock_invoke, client: AsyncClient):
    """Default framework should be gemini when none specified."""
    response = await client.post(
        "/api/v1/agents/invoke",
        json={"prompt": "hello"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "gemini"


async def test_invoke_invalid_framework_returns_422(client: AsyncClient):
    response = await client.post(
        "/api/v1/agents/invoke",
        json={"prompt": "hello", "framework": "nonexistent"},
    )
    assert response.status_code == 422


# ── Strands agent unit tests ─────────────────────────────────────────────


def test_strands_tools_are_importable():
    """Strands tools module loads without errors."""
    from app.agents.strands_tools import ANALYSIS_TOOLS

    assert len(ANALYSIS_TOOLS) >= 5
    names = [t.tool_name for t in ANALYSIS_TOOLS]
    assert "get_findings_summary" in names
    assert "get_department_risk" in names
    assert "get_recent_secrets" in names
    assert "get_chat_stats" in names
    assert "get_dashboard_overview" in names


@patch("app.agents.strands_agent.settings")
def test_build_model_raises_for_unknown_provider(mock_settings):
    """Unknown MODEL_PROVIDER raises ValueError."""
    mock_settings.model_provider = "unknown_provider"

    from app.agents.strands_agent import _build_model

    with pytest.raises(ValueError, match="Unknown MODEL_PROVIDER"):
        _build_model()
