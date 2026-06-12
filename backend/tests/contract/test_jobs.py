"""Contract tests for GET/PATCH /api/jobs — Scout job board endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, PageSnapshot, StatusTransition


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
async def test_get_jobs_filter_by_source_url(test_client: AsyncClient) -> None:
    await _ingest(test_client, source_url="https://example.com/j/40", title="Unique Job")
    resp = await test_client.get("/api/jobs?source_url=https://example.com/j/40")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Unique Job"


@pytest.mark.asyncio
async def test_get_jobs_filter_by_source_url_no_match_returns_empty(
    test_client: AsyncClient,
) -> None:
    resp = await test_client.get("/api/jobs?source_url=https://example.com/does-not-exist")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_jobs_filter_by_source_url_includes_archived(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/41")
    job = await db_session.get(JobListing, ingest_resp["id"])
    assert job is not None
    job.status = "archived"
    await db_session.commit()

    resp = await test_client.get("/api/jobs?source_url=https://example.com/j/41")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "archived"


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


# ---------------------------------------------------------------------------
# Reparse endpoint
# ---------------------------------------------------------------------------


async def _create_job_without_snapshot(db_session: AsyncSession) -> JobListing:
    company = Company(name="SnapshotlessCo")
    db_session.add(company)
    await db_session.flush()
    job = JobListing(
        company_id=company.id,
        title="Original Title",
        location="Remote, US",
        source_url="https://example.com/j/no-snapshot",
        status="saved",
    )
    db_session.add(job)
    await db_session.flush()
    db_session.add(StatusTransition(job_listing_id=job.id, from_status=None, to_status="saved"))
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.mark.asyncio
async def test_reparse_with_no_snapshot_row_returns_404(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _create_job_without_snapshot(db_session)
    resp = await test_client.post(f"/api/jobs/{job.id}/reparse")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reparse_with_empty_snapshot_blob_returns_404(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _create_job_without_snapshot(db_session)
    db_session.add(
        PageSnapshot(
            job_listing_id=job.id,
            html_blob=b"",
            file_path=None,
            content_hash="empty",
            size_bytes=0,
        )
    )
    await db_session.commit()
    resp = await test_client.post(f"/api/jobs/{job.id}/reparse")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reparse_with_valid_snapshot_updates_fields(test_client: AsyncClient) -> None:
    html = (
        "<html><head><title>Ignored</title></head><body>"
        "<h1>Reparsed Title</h1>"
        "<div class='job-description'><p>Updated description text.</p></div>"
        "</body></html>"
    )
    ingest_resp = await _ingest(
        test_client,
        source_url="https://example.com/j/reparse-success",
        title="Original Title",
        description="Original description",
        html=html,
    )
    job_id = ingest_resp["id"]
    resp = await test_client.post(f"/api/jobs/{job_id}/reparse")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Reparsed Title"
    assert "Updated description text" in data["description"]


# ---------------------------------------------------------------------------
# Job note endpoints (US1 + US3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_job_note_returns_404_when_no_note(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/note1")
    job_id = ingest_resp["id"]
    resp = await test_client.get(f"/api/jobs/{job_id}/note")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_job_note_creates_note(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/note2")
    job_id = ingest_resp["id"]
    resp = await test_client.put(f"/api/jobs/{job_id}/note", json={"body": "First note"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"] == "First note"
    assert data["job_listing_id"] == job_id
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_put_job_note_updates_existing_note(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/note3")
    job_id = ingest_resp["id"]
    await test_client.put(f"/api/jobs/{job_id}/note", json={"body": "Original"})
    resp = await test_client.put(f"/api/jobs/{job_id}/note", json={"body": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["body"] == "Updated"


@pytest.mark.asyncio
async def test_get_job_note_returns_existing_note(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/note4")
    job_id = ingest_resp["id"]
    await test_client.put(f"/api/jobs/{job_id}/note", json={"body": "Persisted"})
    resp = await test_client.get(f"/api/jobs/{job_id}/note")
    assert resp.status_code == 200
    assert resp.json()["body"] == "Persisted"


@pytest.mark.asyncio
async def test_delete_job_note_removes_note(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/note5")
    job_id = ingest_resp["id"]
    await test_client.put(f"/api/jobs/{job_id}/note", json={"body": "To delete"})
    resp = await test_client.delete(f"/api/jobs/{job_id}/note")
    assert resp.status_code == 204
    # Subsequent GET must return 404
    resp = await test_client.get(f"/api/jobs/{job_id}/note")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_note_on_missing_note_returns_404(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/note6")
    job_id = ingest_resp["id"]
    resp = await test_client.delete(f"/api/jobs/{job_id}/note")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# has_note field on job list (US2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_jobs_has_note_false_when_no_note(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/hasnote1")
    job_id = ingest_resp["id"]
    resp = await test_client.get("/api/jobs")
    assert resp.status_code == 200
    items = resp.json()["items"]
    job = next(j for j in items if j["id"] == job_id)
    assert job["has_note"] is False


@pytest.mark.asyncio
async def test_get_jobs_has_note_true_after_note_created(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/hasnote2")
    job_id = ingest_resp["id"]
    await test_client.put(f"/api/jobs/{job_id}/note", json={"body": "Some note"})
    resp = await test_client.get("/api/jobs")
    assert resp.status_code == 200
    items = resp.json()["items"]
    job = next(j for j in items if j["id"] == job_id)
    assert job["has_note"] is True
