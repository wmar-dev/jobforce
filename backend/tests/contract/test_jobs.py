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
async def test_get_jobs_filter_by_company_name_substring(test_client: AsyncClient) -> None:
    await _ingest(
        test_client,
        source_url="https://example.com/j/35",
        title="Reddit Job",
        company_name="Reddit",
    )
    resp = await test_client.get("/api/jobs?company=redd")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(item["company"]["name"] == "Reddit" for item in data["items"])


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
async def test_patch_job_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.patch("/api/jobs/99999", json={"location": "Remote"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_job_updates_only_supplied_fields(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(
        test_client,
        source_url="https://example.com/j/patch-partial",
        title="Original Title",
        location="Original Location",
        role_type="full-time",
    )
    job_id = ingest_resp["id"]
    resp = await test_client.patch(f"/api/jobs/{job_id}", json={"location": "New York"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["location"] == "New York"
    assert data["title"] == "Original Title"
    assert data["role_type"] == "full-time"


@pytest.mark.asyncio
async def test_delete_job_removes_job(test_client: AsyncClient) -> None:
    ingest_resp = await _ingest(test_client, source_url="https://example.com/j/delete-me")
    job_id = ingest_resp["id"]
    resp = await test_client.delete(f"/api/jobs/{job_id}")
    assert resp.status_code == 204
    resp = await test_client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.delete("/api/jobs/99999")
    assert resp.status_code == 404
    # Repeating the delete on the same (still-missing) id must also 404.
    resp = await test_client.delete("/api/jobs/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_job_status_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.patch("/api/jobs/99999/status", json={"status": "applied"})
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
# Additional GET /api/jobs filters, sort, and combined queries (US1)
# ---------------------------------------------------------------------------


async def _write_score(client: AsyncClient, job_id: int, score: float, scored: int = 1) -> None:
    resp = await client.patch(
        f"/api/jobs/{job_id}",
        json={"fit_score": score, "fit_scored": scored},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_jobs_filter_by_company_id(test_client: AsyncClient) -> None:
    a = await _ingest(
        test_client, source_url="https://example.com/j/companyid-a", company_name="CompanyIdCoA"
    )
    await _ingest(
        test_client, source_url="https://example.com/j/companyid-b", company_name="CompanyIdCoB"
    )
    resp = await test_client.get(f"/api/jobs?company_id={a['company_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(item["company"]["id"] == a["company_id"] for item in data["items"])


@pytest.mark.asyncio
async def test_get_jobs_filter_by_fit_scored(test_client: AsyncClient) -> None:
    scored = await _ingest(
        test_client, source_url="https://example.com/j/fitscored-yes", title="Scored Job"
    )
    await _write_score(test_client, scored["id"], score=0.7, scored=1)
    await _ingest(
        test_client, source_url="https://example.com/j/fitscored-no", title="Unscored Job"
    )

    resp = await test_client.get("/api/jobs?fit_scored=true")
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["id"] == scored["id"] for item in data["items"])
    assert all(item["fit_scored"] is True for item in data["items"])

    resp = await test_client.get("/api/jobs?fit_scored=false")
    assert resp.status_code == 200
    data = resp.json()
    assert all(item["fit_scored"] is False for item in data["items"])
    assert not any(item["id"] == scored["id"] for item in data["items"])


@pytest.mark.asyncio
async def test_get_jobs_filter_by_min_score(test_client: AsyncClient) -> None:
    low = await _ingest(test_client, source_url="https://example.com/j/minscore-low")
    high = await _ingest(test_client, source_url="https://example.com/j/minscore-high")
    await _write_score(test_client, low["id"], score=0.3)
    await _write_score(test_client, high["id"], score=0.8)

    resp = await test_client.get("/api/jobs?min_score=0.5")
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data["items"]}
    assert high["id"] in ids
    assert low["id"] not in ids


@pytest.mark.asyncio
async def test_get_jobs_filter_by_title_substring(test_client: AsyncClient) -> None:
    match = await _ingest(
        test_client,
        source_url="https://example.com/j/title-match",
        title="Staff Backend Engineer",
    )
    await _ingest(
        test_client,
        source_url="https://example.com/j/title-nomatch",
        title="Marketing Manager",
    )

    resp = await test_client.get("/api/jobs?title=backend")
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data["items"]}
    assert match["id"] in ids
    assert all("backend" in item["title"].lower() for item in data["items"])


@pytest.mark.asyncio
async def test_get_jobs_filter_by_description_substring(test_client: AsyncClient) -> None:
    match = await _ingest(
        test_client,
        source_url="https://example.com/j/desc-match",
        description="Work with distributed systems and Kubernetes.",
    )
    await _ingest(
        test_client,
        source_url="https://example.com/j/desc-nomatch",
        description="Front-end React role.",
    )

    resp = await test_client.get("/api/jobs?q=kubernetes")
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data["items"]}
    assert match["id"] in ids


@pytest.mark.asyncio
async def test_get_jobs_sort_by_company_without_company_filter(test_client: AsyncClient) -> None:
    await _ingest(
        test_client, source_url="https://example.com/j/sortcompany-a", company_name="AlphaSortCo"
    )
    await _ingest(
        test_client, source_url="https://example.com/j/sortcompany-b", company_name="ZetaSortCo"
    )

    resp = await test_client.get("/api/jobs?sort_by=company&sort_dir=asc&limit=200")
    assert resp.status_code == 200
    names = [item["company"]["name"] for item in resp.json()["items"]]
    alpha_idx = names.index("AlphaSortCo")
    zeta_idx = names.index("ZetaSortCo")
    assert alpha_idx < zeta_idx


@pytest.mark.asyncio
async def test_get_jobs_combined_filters_and_sort(test_client: AsyncClient) -> None:
    keep = await _ingest(
        test_client,
        source_url="https://example.com/j/combined-keep",
        company_name="CombinedCo",
        title="Combined Keep Job",
    )
    await _write_score(test_client, keep["id"], score=0.9)
    await _ingest(
        test_client,
        source_url="https://example.com/j/combined-drop-score",
        company_name="CombinedCo",
        title="Combined Drop Job",
    )
    await _ingest(
        test_client,
        source_url="https://example.com/j/combined-drop-company",
        company_name="OtherCombinedCo",
        title="Combined Other Company Job",
    )

    resp = await test_client.get(
        "/api/jobs?company=CombinedCo&min_score=0.5&status=saved&sort_by=fit_score&sort_dir=desc"
    )
    assert resp.status_code == 200
    data = resp.json()
    ids = [item["id"] for item in data["items"]]
    assert ids == [keep["id"]]


@pytest.mark.asyncio
async def test_get_jobs_sort_nulls_last_and_tiebreak(test_client: AsyncClient) -> None:
    scored_low = await _ingest(test_client, source_url="https://example.com/j/nullsort-low")
    scored_high = await _ingest(test_client, source_url="https://example.com/j/nullsort-high")
    unscored = await _ingest(test_client, source_url="https://example.com/j/nullsort-null")
    await _write_score(test_client, scored_low["id"], score=0.3)
    await _write_score(test_client, scored_high["id"], score=0.8)
    # unscored has fit_score left as null

    for sort_dir in ("asc", "desc"):
        resp = await test_client.get(f"/api/jobs?sort_by=fit_score&sort_dir={sort_dir}&limit=200")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        # The null-score job must sort after every non-null-score job, regardless of direction.
        assert ids.index(unscored["id"]) > ids.index(scored_low["id"])
        assert ids.index(unscored["id"]) > ids.index(scored_high["id"])

    tie_older = await _ingest(test_client, source_url="https://example.com/j/tiebreak-older")
    await _write_score(test_client, tie_older["id"], score=0.5)
    tie_newer = await _ingest(test_client, source_url="https://example.com/j/tiebreak-newer")
    await _write_score(test_client, tie_newer["id"], score=0.5)

    resp = await test_client.get("/api/jobs?sort_by=fit_score&sort_dir=desc&limit=200")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    # Equal fit_score ties break by created_at desc — the more recently created job comes first.
    assert ids.index(tie_newer["id"]) < ids.index(tie_older["id"])


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
async def test_reparse_job_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/jobs/99999/reparse")
    assert resp.status_code == 404


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
async def test_get_job_note_not_found_job_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/jobs/99999/note")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_job_note_not_found_job_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.put("/api/jobs/99999/note", json={"body": "orphan note"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_job_note_not_found_job_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.delete("/api/jobs/99999/note")
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
