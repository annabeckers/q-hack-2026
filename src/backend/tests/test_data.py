"""Data endpoint tests — upload, validation, metrics."""

import io

from httpx import AsyncClient


async def test_upload_csv_returns_200(client: AsyncClient):
    csv_content = b"name,age\nAlice,30\nBob,25"
    response = await client.post(
        "/api/v1/data/upload",
        files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.csv"
    assert data["size"] > 0
    assert "status" in data


async def test_upload_unsupported_extension_returns_400(client: AsyncClient):
    response = await client.post(
        "/api/v1/data/upload",
        files={"file": ("hack.exe", io.BytesIO(b"binary"), "application/octet-stream")},
    )
    assert response.status_code == 400
