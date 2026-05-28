"""Integration tests for storage service — BLOB threshold routing and integrity check."""

from __future__ import annotations

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing
from jobforce.services.storage import BLOB_THRESHOLD_BYTES, store_snapshot, verify_integrity


async def _make_job(session: AsyncSession, source_url: str) -> int:
    company = Company(name=f"Co-{source_url[-4:]}")
    session.add(company)
    await session.flush()
    job = JobListing(
        company_id=company.id,
        title="Test Job",
        source_url=source_url,
    )
    session.add(job)
    await session.flush()
    return job.id


@pytest.mark.asyncio
async def test_small_html_stored_as_blob(db_session: AsyncSession, tmp_path: object) -> None:
    job_id = await _make_job(db_session, "https://example.com/s/1")
    html = b"<html>" + b"x" * 100 + b"</html>"
    snapshot = await store_snapshot(
        session=db_session,
        job_listing_id=job_id,
        html_bytes=html,
        pages_dir=str(tmp_path),
    )
    assert snapshot.html_blob == html
    assert snapshot.file_path is None
    assert snapshot.size_bytes == len(html)


@pytest.mark.asyncio
async def test_large_html_stored_as_file(db_session: AsyncSession, tmp_path: object) -> None:
    job_id = await _make_job(db_session, "https://example.com/s/2")
    html = b"<html>" + b"x" * (BLOB_THRESHOLD_BYTES + 1) + b"</html>"
    snapshot = await store_snapshot(
        session=db_session,
        job_listing_id=job_id,
        html_bytes=html,
        pages_dir=str(tmp_path),
    )
    assert snapshot.html_blob is None
    assert snapshot.file_path is not None
    assert os.path.exists(snapshot.file_path)
    assert snapshot.size_bytes == len(html)


@pytest.mark.asyncio
async def test_blob_threshold_boundary(db_session: AsyncSession, tmp_path: object) -> None:
    job_id_at = await _make_job(db_session, "https://example.com/s/3")
    html_at = b"x" * BLOB_THRESHOLD_BYTES
    snap_at = await store_snapshot(
        session=db_session,
        job_listing_id=job_id_at,
        html_bytes=html_at,
        pages_dir=str(tmp_path),
    )
    assert snap_at.html_blob is not None

    job_id_over = await _make_job(db_session, "https://example.com/s/4")
    html_over = b"x" * (BLOB_THRESHOLD_BYTES + 1)
    snap_over = await store_snapshot(
        session=db_session,
        job_listing_id=job_id_over,
        html_bytes=html_over,
        pages_dir=str(tmp_path),
    )
    assert snap_over.file_path is not None


@pytest.mark.asyncio
async def test_verify_integrity_passes_when_file_exists(
    db_session: AsyncSession, tmp_path: object
) -> None:
    job_id = await _make_job(db_session, "https://example.com/s/5")
    html = b"<html>" + b"x" * (BLOB_THRESHOLD_BYTES + 1) + b"</html>"
    snap = await store_snapshot(
        session=db_session,
        job_listing_id=job_id,
        html_bytes=html,
        pages_dir=str(tmp_path),
    )
    issues = await verify_integrity(session=db_session)
    assert snap.file_path not in issues


@pytest.mark.asyncio
async def test_verify_integrity_detects_missing_file(
    db_session: AsyncSession, tmp_path: object
) -> None:
    job_id = await _make_job(db_session, "https://example.com/s/6")
    html = b"<html>" + b"x" * (BLOB_THRESHOLD_BYTES + 1) + b"</html>"
    snap = await store_snapshot(
        session=db_session,
        job_listing_id=job_id,
        html_bytes=html,
        pages_dir=str(tmp_path),
    )
    assert snap.file_path is not None
    os.remove(snap.file_path)

    issues = await verify_integrity(session=db_session)
    assert snap.file_path in issues
