from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from jobforce.db.models import Company, JobListing, StatusTransition


@pytest.mark.asyncio
async def test_status_check_constraint_rejects_invalid(db_session: object) -> None:
    company = Company(name="Test Co")
    db_session.add(company)  # type: ignore[union-attr]
    await db_session.flush()  # type: ignore[union-attr]

    job = JobListing(
        company_id=company.id,
        title="Engineer",
        source_url="https://example.com/job/1",
        status="invalid_status",
    )
    db_session.add(job)  # type: ignore[union-attr]
    with pytest.raises(IntegrityError):
        await db_session.flush()  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_fit_scored_defaults_to_zero(db_session: object) -> None:
    company = Company(name="Defaults Co")
    db_session.add(company)  # type: ignore[union-attr]
    await db_session.flush()  # type: ignore[union-attr]

    job = JobListing(
        company_id=company.id,
        title="Analyst",
        source_url="https://example.com/job/2",
    )
    db_session.add(job)  # type: ignore[union-attr]
    await db_session.commit()  # type: ignore[union-attr]
    await db_session.refresh(job)  # type: ignore[union-attr]

    assert job.fit_scored == 0
    assert job.fit_score is None
    assert job.status == "saved"


@pytest.mark.asyncio
async def test_status_transitions_append_only(db_session: object) -> None:
    company = Company(name="Audit Co")
    db_session.add(company)  # type: ignore[union-attr]
    await db_session.flush()  # type: ignore[union-attr]

    job = JobListing(
        company_id=company.id,
        title="Dev",
        source_url="https://example.com/job/3",
    )
    db_session.add(job)  # type: ignore[union-attr]
    await db_session.flush()  # type: ignore[union-attr]

    t1 = StatusTransition(job_listing_id=job.id, from_status=None, to_status="saved")
    t2 = StatusTransition(job_listing_id=job.id, from_status="saved", to_status="applied")
    db_session.add_all([t1, t2])  # type: ignore[union-attr]
    await db_session.commit()  # type: ignore[union-attr]

    assert t1.id is not None
    assert t2.id is not None
    assert t1.id != t2.id
