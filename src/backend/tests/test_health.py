"""Health endpoint tests."""

from httpx import AsyncClient


async def test_health_returns_200(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


async def test_health_has_status_key(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
