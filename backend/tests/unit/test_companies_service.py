from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, MeetingNote
from jobforce.services.companies import merge_companies


@pytest.mark.asyncio
async def test_merge_companies_reassigns_jobs_and_notes(db_session: AsyncSession) -> None:
    canonical = Company(name="Edison Scientific", domain="edisonscientific.com")
    duplicate = Company(name="Edisonscientific")
    db_session.add_all([canonical, duplicate])
    await db_session.flush()

    job = JobListing(
        company_id=duplicate.id,
        title="Scientific Evals",
        source_url="https://example.com/job/1",
    )
    note = MeetingNote(company_id=duplicate.id, body="Recruiter call notes")
    db_session.add_all([job, note])
    await db_session.commit()

    result = await merge_companies(db_session, source_id=duplicate.id, target_id=canonical.id)

    assert result == {
        "source_id": duplicate.id,
        "target_id": canonical.id,
        "moved_jobs": 1,
        "moved_notes": 1,
    }

    await db_session.refresh(job)
    await db_session.refresh(note)
    assert job.company_id == canonical.id
    assert note.company_id == canonical.id

    remaining = await db_session.execute(select(Company).where(Company.id == duplicate.id))
    assert remaining.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_merge_companies_same_id_raises(db_session: AsyncSession) -> None:
    company = Company(name="Solo Co")
    db_session.add(company)
    await db_session.flush()

    with pytest.raises(ValueError, match="must differ"):
        await merge_companies(db_session, source_id=company.id, target_id=company.id)


@pytest.mark.asyncio
async def test_merge_companies_missing_source_raises(db_session: AsyncSession) -> None:
    target = Company(name="Target Co")
    db_session.add(target)
    await db_session.flush()

    with pytest.raises(ValueError, match="99999 not found"):
        await merge_companies(db_session, source_id=99999, target_id=target.id)


@pytest.mark.asyncio
async def test_merge_companies_missing_target_raises(db_session: AsyncSession) -> None:
    source = Company(name="Source Co")
    db_session.add(source)
    await db_session.flush()

    with pytest.raises(ValueError, match="99999 not found"):
        await merge_companies(db_session, source_id=source.id, target_id=99999)
