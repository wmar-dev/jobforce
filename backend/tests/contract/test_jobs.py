"""Contract tests for GET/PATCH /api/jobs — Scout job board endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _ingest(client: AsyncClient, **overrides: object) -> dict:
    payload = {
        "source_url": "https://jobs.example.com/posting/1",
        "html": "<html>job</html>",
        "title": "Python Engineer",
        "company_name": "TestCo",
        "location": "Remote, US",
        "role_type": "full-time",
        "description": "Python role",
        **overrides,
    }
    resp = await client.post("/api/ingest", json=payload)
    assert resp.status_code in (201, 409)
    return resp.json()


@pytest.mark.asyncio
async def test_get_jobs_returns_paginated_list(test_client: AsyncClient) -> None:
    await _ingest(test_client, source_url="https://example.com/j/1", title="Job A")
    await _ingest(test_client, source_url="https://example.com/j/2", title="Job B")
    resp = await test_client.get("/api/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 2
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_get_jobs_filter_by_status(test_client: AsyncClient) -> None:
    await _ingest(test_client, source_url="https://example.com/j/10", title="Job X")
    resp = await test_client.get("/api/jobs?status=saved")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["status"] == "saved" for item in data["items"])


@pytest.mark.asyncio
async def test_get_jobs_filter_by_location(test_client: AsyncClient) -> None:
    await _ingest(
        test_client,
        source_url="https://example.com/j/20",
        title="SF Job",
        location="San Francisco, CA",
    )
    resp = await test_client.get("/api/jobs?location=San+Francisco")
    assert resp.status_code == 200
    data = resp.json()
    assert any("San Francisco" in (item.get("location") or "") for item in data["items"])


@pytest.mark.asyncio
async def test_get_jobs_filter_by_role_type(test_client: AsyncClient) -> None:
    await _ingest(
        test_client,
        source_url="https://example.com/j/30",
        title="Contract Job",
        role_type="contract",
    )
    resp = await test_client.get("/api/jobs?role_type=contract")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item.get("role_type") == "contract" for item in data["items"])


@pytest.mark.asyncio
async def test_get_job_detail_includes_status_history(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/detail")
    job_id = ingest_resp["id"]
    resp = await test_client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert "status_history" in data
    assert len(data["status_history"]) >= 1
    assert data["status_history"][0]["to_status"] == "saved"


@pytest.mark.asyncio
async def test_get_job_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/jobs/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_job_status_valid_transition(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/patch1")
    job_id = ingest_resp["id"]
    resp = await test_client.patch(f"/api/jobs/{job_id}/status", json={"status": "applied"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "applied"
    assert "transitioned_at" in data


@pytest.mark.asyncio
async def test_patch_job_status_invalid_transition_returns_422(
    test_client: AsyncClient,
) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/patch2")
    job_id = ingest_resp["id"]
    # saved → interviewing is invalid (must go through applied first)
    resp = await test_client.patch(f"/api/jobs/{job_id}/status", json={"status": "interviewing"})
    assert resp.status_code == 422
    assert "INVALID_TRANSITION" in resp.json().get("code", "")


@pytest.mark.asyncio
async def test_patch_job_status_backward_transition_returns_422(
    test_client: AsyncClient,
) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/patch3")
    job_id = ingest_resp["id"]
    await test_client.patch(f"/api/jobs/{job_id}/status", json={"status": "applied"})
    # applied → saved is backward — must be blocked
    resp = await test_client.patch(f"/api/jobs/{job_id}/status", json={"status": "saved"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_jobs_pagination_limit_offset(test_client: AsyncClient) -> None:
    for i in range(5):
        await _ingest(
            test_client,
            source_url=f"https://example.com/j/page{i}",
            title=f"Job {i}",
            company_name="PagingCo",
        )
    resp = await test_client.get("/api/jobs?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 2
