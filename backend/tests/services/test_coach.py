"""Unit tests for coach service — get_session_summary_data direct-DB branches.

These branches have no reachable API path: nothing in the application writes
InterviewSession.overall_summary today, so "a summary was stored" and "a malformed
summary was stored" can only be exercised by seeding the column directly via db_session.
"""

from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import InterviewSession, JobListing
from jobforce.services.coach import get_session_summary_data


@pytest.mark.asyncio
async def test_get_session_summary_data_session_not_found_raises(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(ValueError):
        await get_session_summary_data(db_session, 99999)


@pytest.mark.asyncio
async def test_get_session_summary_data_returns_stored_summary_when_valid_json(
    db_session: AsyncSession, sample_job: JobListing
) -> None:
    stored = {
        "session_id": 1,
        "overall_score": 0.7,
        "summary": "Good progress",
        "areas_to_improve": ["pacing"],
    }
    interview = InterviewSession(
        job_listing_id=sample_job.id,
        session_type="prep",
        questions=json.dumps([{"id": "q1"}]),
        overall_summary=json.dumps(stored),
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    result = await get_session_summary_data(db_session, interview.id)
    assert result == stored


@pytest.mark.asyncio
async def test_get_session_summary_data_returns_default_when_summary_malformed(
    db_session: AsyncSession, sample_job: JobListing
) -> None:
    interview = InterviewSession(
        job_listing_id=sample_job.id,
        session_type="prep",
        questions=json.dumps([{"id": "q1"}]),
        overall_summary="{not valid json",
    )
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)

    result = await get_session_summary_data(db_session, interview.id)
    assert result["overall_score"] == 0.0
    assert result["summary"] == "No answers submitted yet."
    assert result["areas_to_improve"] == []
