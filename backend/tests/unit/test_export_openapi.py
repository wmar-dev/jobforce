from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from jobforce.cli import export_openapi
from jobforce.cli.export_openapi import render_openapi_yaml


def test_render_is_deterministic() -> None:
    assert render_openapi_yaml() == render_openapi_yaml()


def test_render_ends_with_single_newline() -> None:
    out = render_openapi_yaml()
    assert out.endswith("\n")
    assert not out.endswith("\n\n")


def test_render_is_openapi_31() -> None:
    doc = yaml.safe_load(render_openapi_yaml())
    assert str(doc["openapi"]).startswith("3.1")


def test_render_preserves_insertion_order() -> None:
    doc = yaml.safe_load(render_openapi_yaml())
    keys = [k for k in doc if k != "tags"]
    assert keys == ["openapi", "info", "paths", "components"]


def test_render_has_no_servers_block() -> None:
    doc = yaml.safe_load(render_openapi_yaml())
    assert "servers" not in doc


def test_render_needs_no_config(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> Any:
        raise AssertionError("render must not read config")

    import jobforce.config as config_module

    monkeypatch.setattr(config_module, "get_config", _boom)
    assert render_openapi_yaml().startswith("openapi:")


# --- CLI (US1) ---


def test_main_writes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "openapi.yaml"
    monkeypatch.setattr(export_openapi, "OUTPUT_PATH", target)
    assert export_openapi.main([]) == 0
    assert target.read_text(encoding="utf-8") == render_openapi_yaml()


def test_main_check_passes_when_current(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "openapi.yaml"
    target.write_text(render_openapi_yaml(), encoding="utf-8")
    monkeypatch.setattr(export_openapi, "OUTPUT_PATH", target)
    assert export_openapi.main(["--check"]) == 0


def test_main_check_fails_when_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "openapi.yaml"
    target.write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(export_openapi, "OUTPUT_PATH", target)
    assert export_openapi.main(["--check"]) == 1
    assert "out of date" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "stale\n"


def test_main_check_fails_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "openapi.yaml"
    monkeypatch.setattr(export_openapi, "OUTPUT_PATH", target)
    assert export_openapi.main(["--check"]) == 1
    assert not target.exists()
