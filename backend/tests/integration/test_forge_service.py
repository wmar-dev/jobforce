"""Integration tests for Forge service — compute_diff and render_pdf.

tailor_resume() and _call_claude() were removed when AI tailoring moved to the
/forge-tailor skill (Constitution Principle VI). Tests for the skill-driven flow
live in tests/contract/test_forge.py.
"""

from __future__ import annotations

import pytest

from jobforce.services.forge import compute_diff

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


@pytest.mark.asyncio
async def test_compute_diff_returns_changed_fields() -> None:
    tailored = dict(_BASE_DATA)
    tailored["skills"] = ["Python", "FastAPI", "PostgreSQL"]

    diff = compute_diff(_BASE_DATA, tailored)
    assert isinstance(diff, list)
    assert len(diff) >= 1
    skills_diff = next((d for d in diff if d["field"] == "skills"), None)
    assert skills_diff is not None
    assert "original" in skills_diff
    assert "tailored" in skills_diff


@pytest.mark.asyncio
async def test_compute_diff_empty_when_no_changes() -> None:
    diff = compute_diff(_BASE_DATA, _BASE_DATA)
    assert diff == []


@pytest.mark.asyncio
async def test_compute_diff_detects_added_field() -> None:
    tailored = dict(_BASE_DATA)
    tailored["certifications"] = ["AWS Certified"]

    diff = compute_diff(_BASE_DATA, tailored)
    added = next((d for d in diff if d["field"] == "certifications"), None)
    assert added is not None
    assert added["original"] == ""
    assert "AWS Certified" in added["tailored"]


@pytest.mark.asyncio
async def test_compute_diff_detects_removed_field() -> None:
    tailored = {k: v for k, v in _BASE_DATA.items() if k != "education"}

    diff = compute_diff(_BASE_DATA, tailored)
    removed = next((d for d in diff if d["field"] == "education"), None)
    assert removed is not None
    assert removed["tailored"] == ""
    assert "MIT" in removed["original"]
