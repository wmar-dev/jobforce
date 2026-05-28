"""Integration tests for Forge service — tailor_resume, compute_diff, render_pdf."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, Resume

_BASE_DATA = {
    "personal_info": {"name": "John Smith", "email": "john@example.com"},
    "work_history": [
        {
            "title": "Backend Engineer",
            "company": "OldCorp",
            "start_date": "2019-06",
            "bullets": ["Built REST APIs", "Maintained PostgreSQL database"],
        }
    ],
    "education": [{"degree": "B.S. CS", "institution": "MIT"}],
    "skills": ["Python", "Django", "PostgreSQL"],
}


async def _make_job(session: AsyncSession, description: str = "Python FastAPI role") -> JobListing:
    company = Company(name="ForgeTestCo")
    session.add(company)
    await session.flush()
    job = JobListing(
        company_id=company.id,
        title="Senior Backend Engineer",
        source_url="https://example.com/forge/int/1",
        status="saved",
        description=description,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def _make_base_resume(session: AsyncSession) -> Resume:
    resume = Resume(
        label="Base Resume",
        is_base=1,
        structured_data=json.dumps(_BASE_DATA),
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


@pytest.mark.asyncio
async def test_tailor_resume_includes_job_keywords(db_session: AsyncSession) -> None:
    from jobforce.services.forge import tailor_resume

    job = await _make_job(db_session, description="FastAPI microservices with SQLAlchemy")
    resume = await _make_base_resume(db_session)

    mock_response = dict(_BASE_DATA)
    mock_response["skills"] = ["Python", "FastAPI", "SQLAlchemy", "Microservices"]

    with patch(
        "jobforce.services.forge._call_claude",
        new_callable=AsyncMock,
        return_value=json.dumps({"structured_data": mock_response}),
    ):
        result = await tailor_resume(db_session, resume.id, job.id)

    assert result is not None
    assert "structured_data" in result
    tailored_skills = result["structured_data"]["skills"]
    assert "FastAPI" in tailored_skills or "SQLAlchemy" in tailored_skills


@pytest.mark.asyncio
async def test_tailor_resume_does_not_fabricate_work_history(db_session: AsyncSession) -> None:
    from jobforce.services.forge import tailor_resume

    job = await _make_job(db_session, description="Python and cloud architecture")
    resume = await _make_base_resume(db_session)

    mock_response = dict(_BASE_DATA)
    # Simulate Claude adjusting bullets but NOT adding new jobs
    mock_response["work_history"] = [
        {
            "title": "Backend Engineer",
            "company": "OldCorp",
            "start_date": "2019-06",
            "bullets": ["Built REST APIs with FastAPI", "Maintained PostgreSQL database"],
        }
    ]

    with patch(
        "jobforce.services.forge._call_claude",
        new_callable=AsyncMock,
        return_value=json.dumps({"structured_data": mock_response}),
    ):
        result = await tailor_resume(db_session, resume.id, job.id)

    tailored_jobs = result["structured_data"]["work_history"]
    original_jobs = _BASE_DATA["work_history"]
    assert len(tailored_jobs) == len(original_jobs), "Work history count should not change"
    for t, o in zip(tailored_jobs, original_jobs, strict=True):
        assert t["company"] == o["company"], "Company names must not be fabricated"
        assert t["title"] == o["title"], "Job titles must not be fabricated"


@pytest.mark.asyncio
async def test_compute_diff_returns_changed_fields(db_session: AsyncSession) -> None:
    from jobforce.services.forge import compute_diff

    original = dict(_BASE_DATA)
    tailored = dict(_BASE_DATA)
    tailored["skills"] = ["Python", "FastAPI", "PostgreSQL"]

    diff = compute_diff(original, tailored)
    assert isinstance(diff, list)
    assert len(diff) >= 1
    skills_diff = next((d for d in diff if d["field"] == "skills"), None)
    assert skills_diff is not None
    assert "original" in skills_diff
    assert "tailored" in skills_diff


@pytest.mark.asyncio
async def test_compute_diff_empty_when_no_changes(db_session: AsyncSession) -> None:
    from jobforce.services.forge import compute_diff

    diff = compute_diff(_BASE_DATA, _BASE_DATA)
    assert diff == []
