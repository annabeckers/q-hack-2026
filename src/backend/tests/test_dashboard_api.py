"""Dashboard API integration tests."""

from httpx import AsyncClient


async def test_dashboard_summary_returns_kpis(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "findings" in data
    assert "compliance" in data


async def test_cost_analytics_is_session_first(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/analytics/cost", params={"dimension": "department", "cost_basis": "per_session"})
    assert response.status_code == 200
    data = response.json()
    assert data["costBasis"] == "per_session"
    assert data["dimension"] == "department"
    assert isinstance(data["items"], list)
    if data["items"]:
        assert "avgCostPerSession" in data["items"][0]
        assert "sessions" in data["items"][0]


async def test_usage_analytics_reports_avg_word_count(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/analytics/usage", params={"dimension": "model", "metric": "avgWordCountPerSession"})
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "avgWordCountPerSession"
    assert isinstance(data["items"], list)
    if data["items"]:
        assert "averageWordCountPerSession" in data["items"][0]


async def test_security_and_trend_endpoints_shape(client: AsyncClient):
    severity = await client.get("/api/v1/dashboard/security/severity-distribution")
    assert severity.status_code == 200
    severity_data = severity.json()
    assert set(severity_data.keys()) == {"secrets", "pii", "slopsquat"}

    leak_counts = await client.get("/api/v1/dashboard/security/leak-counts", params={"model": "chatgpt", "category": "secret"})
    assert leak_counts.status_code == 200
    assert isinstance(leak_counts.json(), list)

    timeseries = await client.get("/api/v1/dashboard/trends/timeseries", params={"metric": "cost", "granularity": "day"})
    assert timeseries.status_code == 200
    assert "data" in timeseries.json()
