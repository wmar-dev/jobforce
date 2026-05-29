"""Unit tests for oracle service — _build_profile_text and _confidence_label."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from jobforce.services.oracle import _build_profile_text, _confidence_label


def _make_resume(structured_data: dict) -> MagicMock:
    """Return a mock Resume with structured_data as JSON string."""
    r = MagicMock()
    r.structured_data = json.dumps(structured_data)
    return r


_RESUME_DATA = {
    "name": "Jane Doe",
    "skills": ["Python", "FastAPI", "SQLAlchemy"],
    "experience": [
        {"company": "Acme Corp", "title": "Senior Engineer", "dates": "2020-2024"}
    ],
}


def test_build_profile_text_returns_no_resume_message_when_none() -> None:
    result = _build_profile_text(None)
    assert result == "No resume configured."


def test_build_profile_text_returns_json_dump_of_structured_data() -> None:
    resume = _make_resume(_RESUME_DATA)
    result = _build_profile_text(resume)  # type: ignore[arg-type]
    parsed = json.loads(result)
    assert parsed["name"] == "Jane Doe"
    assert "Python" in parsed["skills"]


def test_build_profile_text_includes_all_resume_fields() -> None:
    resume = _make_resume(_RESUME_DATA)
    result = _build_profile_text(resume)  # type: ignore[arg-type]
    assert "Acme Corp" in result
    assert "Senior Engineer" in result
    assert "FastAPI" in result


def test_build_profile_text_handles_malformed_json_gracefully() -> None:
    r = MagicMock()
    r.structured_data = "not valid json {"
    result = _build_profile_text(r)
    assert result == "Resume data could not be read."


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.7, "high"),
        (1.0, "high"),
        (0.4, "medium"),
        (0.69, "medium"),
        (0.39, "low"),
        (0.0, "low"),
    ],
)
def test_confidence_label(score: float, expected: str) -> None:
    assert _confidence_label(score) == expected
