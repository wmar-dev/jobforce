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
