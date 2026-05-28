"""Contract tests for POST /api/ingest — Scout job ingest endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

VALID_PAYLOAD = {
    "source_url": "https://jobs.example.com/posting/123",
    "html": "<html><body>Job posting</body></html>",
    "title": "Senior Python Engineer",
    "company_name": "Acme Corp",
    "location": "Remote, US",
    "role_type": "full-time",
    "description": "We are looking for a senior Python engineer.",
}


@pytest.mark.asyncio
async def test_ingest_valid_payload_returns_201(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/ingest", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["status"] == "saved"
    assert "company_id" in data
    assert data["duplicate"] is False


@pytest.mark.asyncio
async def test_ingest_duplicate_url_returns_409(test_client: AsyncClient) -> None:
    await test_client.post("/api/ingest", json=VALID_PAYLOAD)
    resp = await test_client.post("/api/ingest", json=VALID_PAYLOAD)
    assert resp.status_code == 409
    data = resp.json()
    assert data["duplicate"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_ingest_missing_source_url_returns_422(test_client: AsyncClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "source_url"}
    resp = await test_client.post("/api/ingest", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_missing_title_returns_422(test_client: AsyncClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "title"}
    resp = await test_client.post("/api/ingest", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_missing_company_name_returns_422(test_client: AsyncClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "company_name"}
    resp = await test_client.post("/api/ingest", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_auto_creates_company(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/ingest", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    company_id = resp.json()["company_id"]
    assert isinstance(company_id, int)
    assert company_id > 0


@pytest.mark.asyncio
async def test_ingest_optional_role_type_null(test_client: AsyncClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "role_type"}
    payload["source_url"] = "https://jobs.example.com/posting/456"
    resp = await test_client.post("/api/ingest", json=payload)
    assert resp.status_code == 201
