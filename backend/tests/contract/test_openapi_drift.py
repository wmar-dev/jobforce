from __future__ import annotations

import difflib
from pathlib import Path

import pytest

from jobforce.cli.export_openapi import render_openapi_yaml

SPEC_PATH = Path(__file__).resolve().parents[2] / "openapi.yaml"
STALE_MESSAGE = "openapi.yaml is out of date — run: cd backend && make openapi"


def test_checked_in_spec_matches_code() -> None:
    expected = render_openapi_yaml()
    if not SPEC_PATH.exists():
        pytest.fail(f"{STALE_MESSAGE} (file missing)")
    actual = SPEC_PATH.read_text(encoding="utf-8")
    if actual != expected:
        diff = difflib.unified_diff(
            actual.splitlines(), expected.splitlines(), "checked-in", "generated", lineterm=""
        )
        pytest.fail(STALE_MESSAGE + "\n" + "\n".join(list(diff)[:40]))
