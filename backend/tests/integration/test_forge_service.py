"""Integration tests for Forge service — compute_diff, render_tex_cli, compile_pdf_cli,
export_resume, _slugify, _build_filename_stem, and latex escaping.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jobforce.services.forge import (
    _build_filename_stem,
    _slugify,
    compute_diff,
    export_resume,
    render_tex_cli,
)

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


# ---------------------------------------------------------------------------
# compute_diff (unchanged behaviour)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


def test_slugify_basic() -> None:
    assert _slugify("Acme Corp") == "acme-corp"


def test_slugify_special_chars() -> None:
    assert _slugify("AT&T Inc.") == "at-t-inc"


def test_slugify_multiple_spaces() -> None:
    assert _slugify("Senior   Software   Engineer") == "senior-software-engineer"


def test_slugify_leading_trailing_hyphens() -> None:
    assert _slugify("  -- Acme --  ") == "acme"


def test_slugify_unicode() -> None:
    result = _slugify("Über Corp")
    assert result  # non-empty
    assert not result.startswith("-")
    assert not result.endswith("-")


def test_slugify_all_special() -> None:
    result = _slugify("!@#$%")
    # should produce empty or a safe slug
    assert "-" not in result or result.strip("-") == ""


# ---------------------------------------------------------------------------
# _build_filename_stem
# ---------------------------------------------------------------------------


def test_build_filename_stem_format() -> None:
    stem = _build_filename_stem("Acme Corp", "Senior Engineer")
    assert stem.startswith("resume-acme-corp-senior-engineer-")
    # timestamp portion: YYYYMMDD-HHMMSS = 15 chars
    suffix = stem[len("resume-acme-corp-senior-engineer-") :]
    assert len(suffix) == 15
    assert suffix[8] == "-"


def test_build_filename_stem_two_calls_differ() -> None:
    import time

    stem1 = _build_filename_stem("Acme", "Engineer")
    time.sleep(1.1)
    stem2 = _build_filename_stem("Acme", "Engineer")
    assert stem1 != stem2


# ---------------------------------------------------------------------------
# render_tex_cli
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_tex_cli_produces_tex_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        tex_path = await render_tex_cli(_BASE_DATA, output_dir, "resume-test")
        assert tex_path.exists()
        assert tex_path.suffix == ".tex"
        content = tex_path.read_text()
        assert "John Smith" in content


@pytest.mark.asyncio
async def test_render_tex_cli_escapes_special_chars() -> None:
    data = dict(_BASE_DATA)
    data = {**_BASE_DATA}
    data["personal_info"] = {**_BASE_DATA["personal_info"], "name": "AT&T Employee"}
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = await render_tex_cli(data, Path(tmpdir), "resume-escape-test")
        content = tex_path.read_text()
        # Raw & must not appear unescaped in LaTeX source
        assert r"\&" in content
        assert "AT&T" not in content


@pytest.mark.asyncio
async def test_render_tex_cli_raises_on_missing_template(monkeypatch: pytest.MonkeyPatch) -> None:
    # Patch the scripts dir to a non-existent path to force failure
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("jobforce.services.forge._SCRIPTS_DIR", Path("/nonexistent/path")):
            with pytest.raises(RuntimeError):
                await render_tex_cli(_BASE_DATA, Path(tmpdir), "resume-fail")


# ---------------------------------------------------------------------------
# export_resume
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_resume_returns_tex_path_always(tmp_path: Path) -> None:
    """export_resume always returns a tex_path even when LaTeX unavailable."""

    class FakeResume:
        id = 1
        structured_data = json.dumps(_BASE_DATA)

    with patch("jobforce.services.forge._OUTPUT_DIR", tmp_path):
        with patch(
            "jobforce.services.forge.compile_pdf_cli", new_callable=AsyncMock, return_value=None
        ):
            result = await export_resume(FakeResume(), "Acme Corp", "Senior Engineer")

    assert result.tex_path.endswith(".tex")
    assert result.pdf_path is None


@pytest.mark.asyncio
async def test_export_resume_returns_pdf_path_when_latex_available(tmp_path: Path) -> None:
    class FakeResume:
        id = 1
        structured_data = json.dumps(_BASE_DATA)

    fake_pdf = tmp_path / "resume-test.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4")

    with patch("jobforce.services.forge._OUTPUT_DIR", tmp_path):
        with patch(
            "jobforce.services.forge.compile_pdf_cli", new_callable=AsyncMock, return_value=fake_pdf
        ):
            result = await export_resume(FakeResume(), "Acme Corp", "Senior Engineer")

    assert result.pdf_path is not None
    assert result.pdf_path.endswith(".pdf")
