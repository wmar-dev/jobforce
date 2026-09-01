"""Integration tests for archive/shortlist transitions and bulk archive endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, StatusTransition

# ---------------------------------------------------------------------------
# T013: PATCH /api/jobs/{id}/status → archived (US1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_status_to_archived_records_transition(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_job: JobListing,
) -> None:
    response = await test_client.patch(
        f"/api/jobs/{sample_job.id}/status",
        json={"status": "archived"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "archived"
    assert "transitioned_at" in data

    result = await db_session.execute(
        select(StatusTransition)
        .where(StatusTransition.job_listing_id == sample_job.id)
        .where(StatusTransition.to_status == "archived")
    )
    transition = result.scalar_one_or_none()
    assert transition is not None
    assert transition.from_status == "saved"


# ---------------------------------------------------------------------------
# T021: PATCH archived → shortlisted restores job to active list (US2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_archived_to_shortlisted_not_allowed_directly(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    # Per transition graph: archived → saved → shortlisted; direct archived → shortlisted is blocked
    archived_job = JobListing(
        company_id=sample_company.id,
        title="Archived Job",
        source_url="https://example.com/arc-short",
        status="archived",
    )
    db_session.add(archived_job)
    await db_session.commit()
    await db_session.refresh(archived_job)

    response = await test_client.patch(
        f"/api/jobs/{archived_job.id}/status",
        json={"status": "shortlisted"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_saved_to_shortlisted_then_check_active(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_job: JobListing,
) -> None:
    response = await test_client.patch(
        f"/api/jobs/{sample_job.id}/status",
        json={"status": "shortlisted"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "shortlisted"

    # shortlisted job should appear in default list (not excluded like archived)
    list_response = await test_client.get("/api/jobs")
    assert list_response.status_code == 200
    ids = [j["id"] for j in list_response.json()["items"]]
    assert sample_job.id in ids


# ---------------------------------------------------------------------------
# T027/T028: POST /api/jobs/bulk-archive (US3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bulk_archive_archives_low_score_saved_jobs(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    low_score = JobListing(
        company_id=sample_company.id,
        title="Low Score Job",
        source_url="https://example.com/low",
        status="saved",
        fit_score=0.30,
        fit_scored=1,
    )
    high_score = JobListing(
        company_id=sample_company.id,
        title="High Score Job",
        source_url="https://example.com/high",
        status="saved",
        fit_score=0.75,
        fit_scored=1,
    )
    db_session.add_all([low_score, high_score])
    await db_session.commit()
    await db_session.refresh(low_score)
    await db_session.refresh(high_score)

    response = await test_client.post("/api/jobs/bulk-archive")
    assert response.status_code == 200
    data = response.json()
    assert data["archived_count"] >= 1

    await db_session.refresh(low_score)
    await db_session.refresh(high_score)
    assert low_score.status == "archived"
    assert high_score.status == "saved"


@pytest.mark.asyncio
async def test_bulk_archive_skips_shortlisted_jobs(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    shortlisted_low = JobListing(
        company_id=sample_company.id,
        title="Shortlisted Low Score",
        source_url="https://example.com/short-low",
        status="shortlisted",
        fit_score=0.20,
        fit_scored=1,
    )
    db_session.add(shortlisted_low)
    await db_session.commit()
    await db_session.refresh(shortlisted_low)

    response = await test_client.post("/api/jobs/bulk-archive")
    assert response.status_code == 200

    await db_session.refresh(shortlisted_low)
    assert shortlisted_low.status == "shortlisted"


@pytest.mark.asyncio
async def test_bulk_archive_skips_unscored_jobs(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    unscored = JobListing(
        company_id=sample_company.id,
        title="Unscored Job",
        source_url="https://example.com/unscored",
        status="saved",
        fit_score=None,
        fit_scored=0,
    )
    db_session.add(unscored)
    await db_session.commit()
    await db_session.refresh(unscored)

    await test_client.post("/api/jobs/bulk-archive")

    await db_session.refresh(unscored)
    assert unscored.status == "saved"


@pytest.mark.asyncio
async def test_bulk_archive_skips_pipeline_stage_jobs(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    applied_low = JobListing(
        company_id=sample_company.id,
        title="Applied Low Score",
        source_url="https://example.com/applied-low",
        status="applied",
        fit_score=0.10,
        fit_scored=1,
    )
    db_session.add(applied_low)
    await db_session.commit()
    await db_session.refresh(applied_low)

    await test_client.post("/api/jobs/bulk-archive")

    await db_session.refresh(applied_low)
    assert applied_low.status == "applied"


@pytest.mark.asyncio
async def test_bulk_archive_all_active_archives_regardless_of_score(
    test_client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    high_score = JobListing(
        company_id=sample_company.id,
        title="High Score Job",
        source_url="https://example.com/all-active-high",
        status="saved",
        fit_score=0.90,
        fit_scored=1,
    )
    shortlisted = JobListing(
        company_id=sample_company.id,
        title="Shortlisted Job",
        source_url="https://example.com/all-active-shortlisted",
        status="shortlisted",
        fit_score=0.90,
        fit_scored=1,
    )
    unscored = JobListing(
        company_id=sample_company.id,
        title="Unscored Job",
        source_url="https://example.com/all-active-unscored",
        status="saved",
        fit_score=None,
        fit_scored=0,
    )
    db_session.add_all([high_score, shortlisted, unscored])
    await db_session.commit()
    await db_session.refresh(high_score)
    await db_session.refresh(shortlisted)
    await db_session.refresh(unscored)

    response = await test_client.post(
        f"/api/jobs/bulk-archive?company_id={sample_company.id}&all_active=true"
    )
    assert response.status_code == 200
    assert response.json()["archived_count"] == 3

    for job in (high_score, shortlisted, unscored):
        await db_session.refresh(job)
        assert job.status == "archived"


@pytest.mark.asyncio
async def test_bulk_archive_all_active_requires_company_id(
    test_client: AsyncClient,
) -> None:
    response = await test_client.post("/api/jobs/bulk-archive?all_active=true")
    assert response.status_code == 422
