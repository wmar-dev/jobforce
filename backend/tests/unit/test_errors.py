from __future__ import annotations

from jobforce.routers.errors import BusinessError, ErrorCode, error_responses

_EXPECTED_STATUS = {
    "JOB_NOT_FOUND": 404,
    "NOTE_NOT_FOUND": 404,
    "SNAPSHOT_NOT_FOUND": 404,
    "INVALID_TRANSITION": 422,
    "MISSING_COMPANY_ID": 422,
    "CONFLICTING_OPTIONS": 422,
    "COMPANY_NOT_FOUND": 404,
    "SELF_MERGE": 422,
    "BASE_RESUME_MISSING": 404,
    "RESUME_NOT_FOUND": 404,
    "RANK_RESULT_NOT_FOUND": 404,
    "RANKING_MOVED_TO_SKILL": 501,
    "PREP_SESSION_NOT_FOUND": 404,
    "SESSION_NOT_FOUND": 404,
    "QUESTION_NOT_FOUND": 404,
}


def test_catalog_matches_contract() -> None:
    assert {c.value: c.status for c in ErrorCode} == _EXPECTED_STATUS


def test_single_code_uses_business_error_model() -> None:
    responses = error_responses(ErrorCode.JOB_NOT_FOUND)
    assert list(responses) == [404]
    assert responses[404]["model"] is BusinessError
    assert "JOB_NOT_FOUND" in responses[404]["description"]


def test_same_status_codes_merge() -> None:
    responses = error_responses(ErrorCode.JOB_NOT_FOUND, ErrorCode.NOTE_NOT_FOUND)
    assert list(responses) == [404]
    desc = responses[404]["description"]
    assert "JOB_NOT_FOUND" in desc
    assert "NOTE_NOT_FOUND" in desc


def test_422_documents_both_shapes() -> None:
    responses = error_responses(ErrorCode.SELF_MERGE)
    schema = responses[422]["content"]["application/json"]["schema"]
    refs = {s["$ref"] for s in schema["anyOf"]}
    assert refs == {
        "#/components/schemas/BusinessError",
        "#/components/schemas/HTTPValidationError",
    }
    assert "SELF_MERGE" in responses[422]["description"]


def test_business_error_schema_lists_codes() -> None:
    schema = BusinessError.model_json_schema()
    code = schema["properties"]["code"]
    if "$ref" in code:
        code = schema["$defs"][code["$ref"].rsplit("/", 1)[-1]]
    assert set(code["enum"]) == set(_EXPECTED_STATUS)
