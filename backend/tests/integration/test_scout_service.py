"""Integration tests for Scout service — dedup, company auto-create, storage routing."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, PageSnapshot, StatusTransition
from jobforce.services.scout import IngestPayload, ingest_listing


@pytest.mark.asyncio
async def test_ingest_creates_job_and_company(db_session: AsyncSession) -> None:
    payload = IngestPayload(
        source_url="https://example.com/job/1",
        html="<html>job</html>",
        title="Python Engineer",
        company_name="NewCo",
        location="Remote",
    )
    result = await ingest_listing(db_session, payload)
    assert result["duplicate"] is False
    assert result["status"] == "saved"

    job = await db_session.get(JobListing, result["id"])
    assert job is not None
    assert job.title == "Python Engineer"
    assert job.status == "saved"

    company = await db_session.get(Company, result["company_id"])
    assert company is not None
    assert company.name == "NewCo"


@pytest.mark.asyncio
async def test_dedup_by_url_returns_existing(db_session: AsyncSession) -> None:
    payload = IngestPayload(
        source_url="https://example.com/job/dup",
        html="<html>job</html>",
        title="Engineer",
        company_name="DupCo",
    )
    first = await ingest_listing(db_session, payload)
    second = await ingest_listing(db_session, payload)

    assert first["id"] == second["id"]
    assert second["duplicate"] is True

    result = await db_session.execute(
        select(JobListing).where(JobListing.source_url == payload.source_url)
    )
    jobs = result.scalars().all()
    assert len(jobs) == 1


@pytest.mark.asyncio
async def test_company_auto_created_case_insensitive(db_session: AsyncSession) -> None:
    payload = IngestPayload(
        source_url="https://example.com/job/ci",
        html="<html>job</html>",
        title="Analyst",
        company_name="  acme CORP  ",
    )
    result = await ingest_listing(db_session, payload)
    assert result["duplicate"] is False

    payload2 = IngestPayload(
        source_url="https://example.com/job/ci2",
        html="<html>job2</html>",
        title="Manager",
        company_name="Acme Corp",
    )
    result2 = await ingest_listing(db_session, payload2)
    assert result["company_id"] == result2["company_id"]


@pytest.mark.asyncio
async def test_initial_status_transition_recorded(db_session: AsyncSession) -> None:
    payload = IngestPayload(
        source_url="https://example.com/job/trans",
        html="<html>job</html>",
        title="Dev",
        company_name="TransCo",
    )
    result = await ingest_listing(db_session, payload)
    transitions = await db_session.execute(
        select(StatusTransition).where(StatusTransition.job_listing_id == result["id"])
    )
    rows = transitions.scalars().all()
    assert len(rows) == 1
    assert rows[0].from_status is None
    assert rows[0].to_status == "saved"


@pytest.mark.asyncio
async def test_snapshot_stored_for_small_html(db_session: AsyncSession) -> None:
    payload = IngestPayload(
        source_url="https://example.com/job/snap",
        html="<html>small html</html>",
        title="Snap Job",
        company_name="SnapCo",
    )
    result = await ingest_listing(db_session, payload)
    snap = await db_session.execute(
        select(PageSnapshot).where(PageSnapshot.job_listing_id == result["id"])
    )
    snapshot = snap.scalar_one_or_none()
    assert snapshot is not None
    assert snapshot.html_blob is not None
    assert snapshot.file_path is None
