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
async def test_get_base_resume_returns_empty_or_existing(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/resume/base")
    # Before any resume is uploaded, should return 404 or an empty resume
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_put_base_resume_saves_structured_data(test_client: AsyncClient) -> None:
    resp = await test_client.put("/api/resume/base", json=_BASE_RESUME_DATA)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["is_base"] is True
    assert data["structured_data"]["personal_info"]["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_tailor_resume_returns_tailored_variant_with_diff(
    test_client: AsyncClient,
) -> None:
    base = await _put_base_resume(test_client)
    job = await _ingest_job(test_client)

    mock_tailored = dict(_BASE_RESUME_DATA)
    mock_tailored["skills"] = ["Python", "FastAPI", "SQL", "REST APIs"]
    mock_diff = [
        {
            "field": "skills",
            "original": str(_BASE_RESUME_DATA["skills"]),
            "tailored": str(mock_tailored["skills"]),
        }
    ]

    with patch(
        "jobforce.routers.forge.tailor_resume",
        new_callable=AsyncMock,
        return_value={"structured_data": mock_tailored, "diff": mock_diff},
    ):
        resp = await test_client.post(
            "/api/resume/tailor",
            json={"job_id": job["id"], "base_resume_id": base["id"]},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "diff" in data
    assert isinstance(data["diff"], list)
    assert len(data["diff"]) >= 1
    diff_item = data["diff"][0]
    assert "field" in diff_item
    assert "original" in diff_item
    assert "tailored" in diff_item


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
async def test_tailor_with_missing_job_returns_404(test_client: AsyncClient) -> None:
    base = await _put_base_resume(test_client)
    resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": 99999, "base_resume_id": base["id"]},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_pdf_performance_within_30s(test_client: AsyncClient) -> None:
    """SC-008: PDF export must complete within 30 seconds."""
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
