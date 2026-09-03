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
