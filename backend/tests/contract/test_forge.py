"""Contract tests for Forge resume endpoints."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

_BASE_RESUME_DATA = {
    "personal_info": {
        "name": "Jane Doe",
        "email": "jane@example.com",
    },
    "work_history": [
        {
            "title": "Software Engineer",
            "company": "Acme Corp",
            "start_date": "2020-01",
            "bullets": ["Built APIs with Python", "Led team of 3"],
        }
    ],
    "education": [
        {
            "degree": "B.S. Computer Science",
            "institution": "State University",
        }
    ],
    "skills": ["Python", "FastAPI", "SQL"],
}

_TAILORED_RESUME_DATA = {
    **_BASE_RESUME_DATA,
    "skills": ["Python", "FastAPI", "SQL", "REST APIs"],
}


async def _put_base_resume(client: AsyncClient) -> dict:
    resp = await client.put("/api/resume/base", json=_BASE_RESUME_DATA)
    assert resp.status_code == 200
    return resp.json()


async def _ingest_job(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/ingest",
        json={
            "source_url": "https://example.com/forge/job1",
            "html": "<html>job</html>",
            "title": "Senior Python Engineer",
            "company_name": "TechCo",
            "description": "Looking for Python expert with FastAPI and SQL skills.",
        },
    )
    assert resp.status_code in (201, 409)
    return resp.json()


@pytest.mark.asyncio
async def test_get_base_resume_returns_404_when_empty(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/resume/base")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_base_resume_returns_200_after_upload(test_client: AsyncClient) -> None:
    await _put_base_resume(test_client)
    resp = await test_client.get("/api/resume/base")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_base"] is True
    assert data["structured_data"]["personal_info"]["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_put_base_resume_saves_structured_data(test_client: AsyncClient) -> None:
    resp = await test_client.put("/api/resume/base", json=_BASE_RESUME_DATA)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["is_base"] is True
    assert data["structured_data"]["personal_info"]["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_tailor_resume_accepts_structured_data_from_skill(
    test_client: AsyncClient,
) -> None:
    """Skill performs AI tailoring and POSTs the result; backend stores and diffs."""
    await _put_base_resume(test_client)
    job = await _ingest_job(test_client)

    resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": job["id"], "structured_data": _TAILORED_RESUME_DATA},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["is_base"] is False
    assert data["job_listing_id"] == job["id"]
    assert "diff" in data
    assert isinstance(data["diff"], list)
    assert len(data["diff"]) >= 1
    skills_diff = next((d for d in data["diff"] if d["field"] == "skills"), None)
    assert skills_diff is not None
    assert "original" in skills_diff
    assert "tailored" in skills_diff


@pytest.mark.asyncio
async def test_tailor_resume_no_diff_when_data_unchanged(test_client: AsyncClient) -> None:
    """If skill sends identical data, diff is empty."""
    await _put_base_resume(test_client)
    job = await _ingest_job(test_client)

    resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": job["id"], "structured_data": _BASE_RESUME_DATA},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["diff"] == []


@pytest.mark.asyncio
async def test_tailor_resume_returns_404_when_no_base_resume(
    test_client: AsyncClient,
) -> None:
    """No base resume → 404 with helpful message."""
    job = await _ingest_job(test_client)
    resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": job["id"], "structured_data": _TAILORED_RESUME_DATA},
    )
    assert resp.status_code == 404
    assert "base resume" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tailor_with_missing_job_returns_404(test_client: AsyncClient) -> None:
    await _put_base_resume(test_client)
    resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": 99999, "structured_data": _TAILORED_RESUME_DATA},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_resume_returns_pdf_bytes(test_client: AsyncClient) -> None:
    base = await _put_base_resume(test_client)

    fake_pdf = b"%PDF-1.4 fake content"

    with patch(
        "jobforce.routers.forge.render_pdf",
        new_callable=AsyncMock,
        return_value=fake_pdf,
    ):
        resp = await test_client.post(f"/api/resume/{base['id']}/export")

    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/pdf")
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_export_resume_returns_503_when_latex_unavailable(
    test_client: AsyncClient,
) -> None:
    base = await _put_base_resume(test_client)

    with patch(
        "jobforce.routers.forge.render_pdf",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LaTeX not available"),
    ):
        resp = await test_client.post(f"/api/resume/{base['id']}/export")

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_export_resume_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/resume/99999/export")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_pdf_performance_within_30s(test_client: AsyncClient) -> None:
    import shutil

    import pytest as _pytest

    if not shutil.which("latexmk"):
        _pytest.skip("LaTeX not installed — skipping performance test")

    base = await _put_base_resume(test_client)
    start = time.monotonic()
    resp = await test_client.post(f"/api/resume/{base['id']}/export")
    elapsed = time.monotonic() - start
    assert resp.status_code in (200, 503)
    assert elapsed <= 30.0, f"PDF export took {elapsed:.1f}s, exceeding 30s limit"
