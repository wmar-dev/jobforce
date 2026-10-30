"""Unit tests for jobforce.cli.scout_fetch timeout and error behaviour."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_fetch(args: list[str], timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "jobforce.cli.scout_fetch", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent.parent,  # backend/
    )


def test_missing_url_arg_exits_nonzero() -> None:
    result = _run_fetch([])
    assert result.returncode != 0


def test_invalid_url_exits_nonzero() -> None:
    result = _run_fetch(["--url", "not-a-url"])
    assert result.returncode != 0
    assert result.stderr  # error message on stderr


# ---------------------------------------------------------------------------
# CLI — _validate_url
# ---------------------------------------------------------------------------


def test_validate_url_accepts_https() -> None:
    from jobforce.cli.scout_fetch import _validate_url

    assert (
        _validate_url("https://jobs.example.com/posting/123")
        == "https://jobs.example.com/posting/123"
    )


def test_validate_url_accepts_http() -> None:
    from jobforce.cli.scout_fetch import _validate_url

    assert (
        _validate_url("http://jobs.example.com/posting/123")
        == "http://jobs.example.com/posting/123"
    )


def test_validate_url_rejects_no_scheme() -> None:
    import argparse

    import pytest

    from jobforce.cli.scout_fetch import _validate_url

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_url("jobs.example.com/posting/123")


def test_validate_url_rejects_ftp_scheme() -> None:
    import argparse

    import pytest

    from jobforce.cli.scout_fetch import _validate_url

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_url("ftp://jobs.example.com/posting/123")


def test_validate_url_rejects_empty_netloc() -> None:
    import argparse

    import pytest

    from jobforce.cli.scout_fetch import _validate_url

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_url("https://")


# ---------------------------------------------------------------------------
# CLI — _normalize_ashby_embed_url
# ---------------------------------------------------------------------------


def test_normalize_ashby_embed_url_rewrites_careers_query_param() -> None:
    from jobforce.cli.scout_fetch import _normalize_ashby_embed_url

    url = "https://www.ashbyhq.com/careers?ashby_jid=751768c6-8d97-4e91-a57d-6b85ce4b5a37"
    assert (
        _normalize_ashby_embed_url(url)
        == "https://jobs.ashbyhq.com/Ashby/751768c6-8d97-4e91-a57d-6b85ce4b5a37"
    )


def test_normalize_ashby_embed_url_without_www() -> None:
    from jobforce.cli.scout_fetch import _normalize_ashby_embed_url

    url = "https://ashbyhq.com/careers?ashby_jid=abc123"
    assert _normalize_ashby_embed_url(url) == "https://jobs.ashbyhq.com/Ashby/abc123"


def test_normalize_ashby_embed_url_leaves_jobs_subdomain_unchanged() -> None:
    from jobforce.cli.scout_fetch import _normalize_ashby_embed_url

    url = "https://jobs.ashbyhq.com/figma/abc123"
    assert _normalize_ashby_embed_url(url) == url


def test_normalize_ashby_embed_url_leaves_unrelated_urls_unchanged() -> None:
    from jobforce.cli.scout_fetch import _normalize_ashby_embed_url

    url = "https://factory.com/careers/software-engineer-product"
    assert _normalize_ashby_embed_url(url) == url


def test_normalize_ashby_embed_url_leaves_careers_without_jid_unchanged() -> None:
    from jobforce.cli.scout_fetch import _normalize_ashby_embed_url

    url = "https://www.ashbyhq.com/careers"
    assert _normalize_ashby_embed_url(url) == url


# ---------------------------------------------------------------------------
# Greenhouse boards whose job URLs 302 to the company's own careers page
# (e.g. job-boards.greenhouse.io/unconventionalinc/jobs/<id> ->
# unconv.ai/careers/?gh_jid=<id>, a JS embed scout_fetch can't see into)
# ---------------------------------------------------------------------------


def test_greenhouse_board_job_ref_parses_job_boards_url() -> None:
    from jobforce.cli.scout_fetch import _greenhouse_board_job_ref

    url = "https://job-boards.greenhouse.io/unconventionalinc/jobs/4393750009"
    assert _greenhouse_board_job_ref(url) == ("unconventionalinc", "4393750009")


def test_greenhouse_board_job_ref_parses_legacy_boards_url() -> None:
    from jobforce.cli.scout_fetch import _greenhouse_board_job_ref

    url = "https://boards.greenhouse.io/acme/jobs/123?gh_src=x"
    assert _greenhouse_board_job_ref(url) == ("acme", "123")


def test_greenhouse_board_job_ref_ignores_other_urls() -> None:
    from jobforce.cli.scout_fetch import _greenhouse_board_job_ref

    assert _greenhouse_board_job_ref("https://unconv.ai/careers/?gh_jid=4393750009") is None
    assert (
        _greenhouse_board_job_ref("https://boards.greenhouse.io/embed/job_app?for=x&token=1")
        is None
    )
    assert _greenhouse_board_job_ref("https://job-boards.greenhouse.io/acme") is None


_UNCONV_API_JOB = {
    "title": "Member of Technical Staff - AI Training Platform",
    "company_name": "Unconventional, Inc.",
    "location": {"name": "Mountain View, CA or Greater Seattle Area"},
    "first_published": "2026-09-02T19:00:41-04:00",
    # The boards API returns `content` HTML-entity-escaped.
    "content": "&lt;p&gt;Build the platform that trains our models &amp; more.&lt;/p&gt;",
}


def test_greenhouse_api_job_html_parses_via_greenhouse_adapter() -> None:
    from jobforce.cli.scout_fetch import _greenhouse_api_job_html
    from jobforce.services.parse import parse_html

    html = _greenhouse_api_job_html(_UNCONV_API_JOB)
    result = parse_html(html, "https://job-boards.greenhouse.io/unconventionalinc/jobs/4393750009")
    assert result["title"] == "Member of Technical Staff - AI Training Platform"
    assert result["location"] == "Mountain View, CA or Greater Seattle Area"
    assert result["company_name"] == "Unconventional"
    assert result["posted_at"] == "2026-09-02"
    assert result["description"] is not None
    assert "Build the platform that trains our models & more." in result["description"]


def test_greenhouse_api_job_html_escapes_title() -> None:
    from jobforce.cli.scout_fetch import _greenhouse_api_job_html
    from jobforce.services.parse import parse_html

    html = _greenhouse_api_job_html({**_UNCONV_API_JOB, "title": "R&D <Lead>"})
    result = parse_html(html, "https://job-boards.greenhouse.io/unconventionalinc/jobs/1")
    assert result["title"] == "R&D <Lead>"
