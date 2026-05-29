"""Integration tests: updating the base resume is reflected in oracle and forge immediately."""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Resume
from jobforce.services.oracle import _build_profile_text

_RESUME_V1 = {
    "name": "Bob Dev",
    "skills": ["Python", "Django"],
    "experience": [{"company": "StartupA", "title": "Engineer", "dates": "2018-2022"}],
}

_RESUME_V2 = {
    "name": "Bob Dev",
    "skills": ["Python", "FastAPI", "Rust"],
    "experience": [{"company": "StartupA", "title": "Senior Engineer", "dates": "2018-2024"}],
}


async def _seed_resume(session: AsyncSession, data: dict) -> Resume:
    resume = Resume(label="Base Resume", is_base=1, structured_data=json.dumps(data))
    session.add(resume)
    await session.commit()
    await session.refresh(resume)
    return resume


@pytest.mark.asyncio
async def test_updated_resume_reflected_in_oracle_prompt(db_session: AsyncSession) -> None:
    """After PUT /resume/base, oracle's profile text uses the new content."""
    resume = await _seed_resume(db_session, _RESUME_V1)

    # Simulate PUT /resume/base updating the resume
    resume.structured_data = json.dumps(_RESUME_V2)
    await db_session.commit()
    await db_session.refresh(resume)

    profile_text = _build_profile_text(resume)
    parsed = json.loads(profile_text)
    assert "FastAPI" in parsed["skills"]
    assert "Rust" in parsed["skills"]
    assert "Django" not in parsed["skills"]


@pytest.mark.asyncio
async def test_updated_resume_reflected_in_forge_diff(test_client: AsyncClient) -> None:
    """After PUT /resume/base with new data, POST /resume/tailor diffs against updated base."""
    await test_client.put("/api/resume/base", json=_RESUME_V1)

    # Ingest a job to tailor against
    job_resp = await test_client.post(
        "/api/ingest",
        json={
            "source_url": "https://example.com/consistency/job1",
            "html": "<html>job</html>",
            "title": "Rust Backend Engineer",
            "company_name": "RustCo",
            "description": "Looking for Rust and FastAPI experience.",
        },
    )
    assert job_resp.status_code in (201, 409)
    job = job_resp.json()

    # Update the base resume
    update_resp = await test_client.put("/api/resume/base", json=_RESUME_V2)
    assert update_resp.status_code == 200

    # Tailor using V2 data (unchanged from base → diff should be empty)
    tailor_resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": job["id"], "structured_data": _RESUME_V2},
    )
    assert tailor_resp.status_code == 200
    data = tailor_resp.json()
    # No diff because skill sent the same data as the updated base
    assert data["diff"] == []


@pytest.mark.asyncio
async def test_forge_diff_shows_changes_relative_to_current_base(
    test_client: AsyncClient,
) -> None:
    """Diff is always computed against the current base, not a stale snapshot."""
    await test_client.put("/api/resume/base", json=_RESUME_V1)

    job_resp = await test_client.post(
        "/api/ingest",
        json={
            "source_url": "https://example.com/consistency/job2",
            "html": "<html>job</html>",
            "title": "Python Engineer",
            "company_name": "PyCo",
            "description": "Python and FastAPI role.",
        },
    )
    job = job_resp.json()

    # Skill tailors and adds FastAPI to skills
    tailored = dict(_RESUME_V1)
    tailored["skills"] = ["Python", "Django", "FastAPI"]

    tailor_resp = await test_client.post(
        "/api/resume/tailor",
        json={"job_id": job["id"], "structured_data": tailored},
    )
    assert tailor_resp.status_code == 200
    diff = tailor_resp.json()["diff"]
    skills_diff = next((d for d in diff if d["field"] == "skills"), None)
    assert skills_diff is not None
    assert "FastAPI" in skills_diff["tailored"]
