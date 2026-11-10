"""Every operation in the generated spec is fully documented (contracts/tooling.md rules 1–9)."""

from __future__ import annotations

import tomllib
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Any

import pytest
import yaml

from jobforce.cli.export_openapi import render_openapi_yaml
from jobforce.routers.errors import ErrorCode

_BUSINESS_REF = "#/components/schemas/BusinessError"
_VALIDATION_REF = "#/components/schemas/HTTPValidationError"
_RESUME_KEYS = {
    "personal_info",
    "summary",
    "skills",
    "work_history",
    "education",
    "projects",
    "certifications",
    "coursework",
    "patents",
}
# Responses that are deliberately not BusinessError: ingest answers a duplicate with
# 409 + the existing listing's IngestResponse, which callers use to find the job.
_NON_ERROR_BODY_RESPONSES = {("POST", "/api/ingest", "409")}


@cache
def _spec() -> dict[str, Any]:
    doc: dict[str, Any] = yaml.safe_load(render_openapi_yaml())
    return doc


def _operations() -> Iterator[tuple[str, str, dict[str, Any]]]:
    for path, ops in _spec()["paths"].items():
        for method, op in ops.items():
            yield method.upper(), path, op


_OPS = list(_operations())
_IDS = [f"{m} {p}" for m, p, _ in _OPS]


def _json_schema(response: dict[str, Any]) -> dict[str, Any] | None:
    schema: dict[str, Any] | None = (
        response.get("content", {}).get("application/json", {}).get("schema")
    )
    return schema


@pytest.mark.parametrize(("method", "path", "op"), _OPS, ids=_IDS)
def test_rule1_summary(method: str, path: str, op: dict[str, Any]) -> None:
    summary = op.get("summary", "")
    assert summary, f"{method} {path}: missing summary"
    assert len(summary) <= 80, f"{method} {path}: summary longer than 80 chars"


@pytest.mark.parametrize(("method", "path", "op"), _OPS, ids=_IDS)
def test_rule2_description(method: str, path: str, op: dict[str, Any]) -> None:
    assert op.get("description", "").strip(), f"{method} {path}: missing description"


@pytest.mark.parametrize(("method", "path", "op"), _OPS, ids=_IDS)
def test_rule3_single_described_tag(method: str, path: str, op: dict[str, Any]) -> None:
    tags = op.get("tags", [])
    assert len(tags) == 1, f"{method} {path}: expected exactly one tag, got {tags}"
    described = {t["name"] for t in _spec().get("tags", []) if t.get("description")}
    assert tags[0] in described, f"{method} {path}: tag '{tags[0]}' has no description"


@pytest.mark.parametrize(("method", "path", "op"), _OPS, ids=_IDS)
def test_rule4_typed_success(method: str, path: str, op: dict[str, Any]) -> None:
    responses = op["responses"]
    success = [s for s in responses if s.startswith("2")]
    # A deprecated stub that only ever answers with an error has no success response.
    if op.get("deprecated") and not success:
        return
    assert success, f"{method} {path}: no 2xx response"
    for status in success:
        schema = _json_schema(responses[status])
        if status == "204":
            assert "content" not in responses[status], f"{method} {path}: 204 has content"
        else:
            assert schema, f"{method} {path}: {status} response has no schema"


@pytest.mark.parametrize(("method", "path", "op"), _OPS, ids=_IDS)
def test_rule5_parameter_descriptions(method: str, path: str, op: dict[str, Any]) -> None:
    for param in op.get("parameters", []):
        assert param.get("description", "").strip(), (
            f"{method} {path}: parameter '{param['name']}' has no description"
        )


@pytest.mark.parametrize(("method", "path", "op"), _OPS, ids=_IDS)
def test_rule6_error_shapes(method: str, path: str, op: dict[str, Any]) -> None:
    for status, response in op["responses"].items():
        if int(status) < 400 or (method, path, status) in _NON_ERROR_BODY_RESPONSES:
            continue
        schema = _json_schema(response) or {}
        if status == "422":
            assert not (schema.get("anyOf") and schema.get("$ref")), (
                f"{method} {path}: 422 has a $ref beside anyOf (ambiguous shape)"
            )
            refs = {s.get("$ref") for s in schema.get("anyOf", [])} or {schema.get("$ref")}
            assert refs in ({_VALIDATION_REF}, {_BUSINESS_REF, _VALIDATION_REF}), (
                f"{method} {path}: 422 must be HTTPValidationError or anyOf both shapes"
            )
        else:
            assert schema.get("$ref") == _BUSINESS_REF, (
                f"{method} {path}: {status} response must reference BusinessError"
            )


def test_rule7_error_code_enum_matches_catalog() -> None:
    schemas = _spec()["components"]["schemas"]
    code = schemas["BusinessError"]["properties"]["code"]
    if "$ref" in code:
        code = schemas[code["$ref"].rsplit("/", 1)[-1]]
    assert code["enum"] == [c.value for c in ErrorCode]


def test_rule8_resume_structured_data_documented() -> None:
    schema = _spec()["components"]["schemas"]["ResumeStructuredData"]
    assert set(schema["properties"]) == _RESUME_KEYS
    assert not schema.get("required")


def test_rule9_info_title_and_version() -> None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    version = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]
    info = _spec()["info"]
    assert info["title"] == "Jobforce API"
    assert info["version"] == version
