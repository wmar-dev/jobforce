"""Integration test: base resume structured_data flows into oracle prompt building."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Resume
from jobforce.services.oracle import _build_profile_text

_RESUME_DATA = {
    "name": "Alice Engineer",
    "skills": ["Go", "Kubernetes", "gRPC"],
    "experience": [{"company": "CloudCo", "title": "Platform Engineer", "dates": "2021-2024"}],
    "summary": "Platform engineer specialising in distributed systems.",
}


async def _seed_base_resume(session: AsyncSession, data: dict) -> Resume:
    resume = Resume(label="Base Resume", is_base=1, structured_data=json.dumps(data))
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


@pytest.mark.asyncio
async def test_oracle_profile_text_contains_resume_content(db_session: AsyncSession) -> None:
    """_build_profile_text with a Resume returns the resume's structured_data as JSON."""
    resume = await _seed_base_resume(db_session, _RESUME_DATA)
    profile_text = _build_profile_text(resume)

    parsed = json.loads(profile_text)
    assert parsed["name"] == "Alice Engineer"
    assert "Kubernetes" in parsed["skills"]
    assert parsed["experience"][0]["company"] == "CloudCo"


@pytest.mark.asyncio
async def test_oracle_profile_text_none_when_no_resume() -> None:
    """Without a resume, _build_profile_text returns the no-resume sentinel."""
    result = _build_profile_text(None)
    assert result == "No resume configured."


@pytest.mark.asyncio
async def test_oracle_prompt_includes_resume_data(db_session: AsyncSession) -> None:
    """The full ranking prompt contains the resume content."""
    from jobforce.db.models import Company, JobListing
    from jobforce.services.oracle import _build_ranking_prompt

    resume = await _seed_base_resume(db_session, _RESUME_DATA)

    company = Company(name="TestOrg")
    db_session.add(company)
    await db_session.flush()
    job = JobListing(
        company_id=company.id,
        title="Platform Engineer",
        source_url="https://jobs.example.com/pe/1",
        status="saved",
        description="We need a platform engineer with Kubernetes expertise.",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    profile_text = _build_profile_text(resume)
    prompt = _build_ranking_prompt(profile_text, job, job.description or "")

    assert "Alice Engineer" in prompt
    assert "Kubernetes" in prompt
    assert "Platform Engineer" in prompt
