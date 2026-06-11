from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, MeetingNote

logger = logging.getLogger(__name__)


async def merge_companies(session: AsyncSession, source_id: int, target_id: int) -> dict[str, Any]:
    """Merge `source_id` into `target_id`: reassign job listings and meeting
    notes, then delete the `source_id` company record.

    Use to clean up duplicate Company rows created when an ingest's parsed
    `company_name` doesn't exactly match an existing company's name (e.g.
    "Edisonscientific" vs "Edison Scientific").
    """
    if source_id == target_id:
        raise ValueError("source_id and target_id must differ")

    source = await session.get(Company, source_id)
    if source is None:
        raise ValueError(f"Company {source_id} not found")
    target = await session.get(Company, target_id)
    if target is None:
        raise ValueError(f"Company {target_id} not found")

    job_result = await session.execute(select(JobListing).where(JobListing.company_id == source_id))
    jobs = job_result.scalars().all()
    for job in jobs:
        job.company_id = target_id

    note_result = await session.execute(
        select(MeetingNote).where(MeetingNote.company_id == source_id)
    )
    notes = note_result.scalars().all()
    for note in notes:
        note.company_id = target_id

    await session.delete(source)
    await session.commit()

    logger.info(
        "Merged company id=%d (%r) into id=%d (%r): %d jobs, %d notes",
        source_id,
        source.name,
        target_id,
        target.name,
        len(jobs),
        len(notes),
    )
    return {
        "source_id": source_id,
        "target_id": target_id,
        "moved_jobs": len(jobs),
        "moved_notes": len(notes),
    }
