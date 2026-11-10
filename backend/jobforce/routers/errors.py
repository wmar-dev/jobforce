"""Business-error catalog shared by runtime responses and the OpenAPI document.

One ``ErrorCode`` list drives both what routes return (``{detail, code}``) and what
the spec documents, so the two cannot drift. Codes are append-only: consumers
(skills, frontend) branch on ``code`` and never on ``detail`` text.
"""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(StrEnum):
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    NOTE_NOT_FOUND = "NOTE_NOT_FOUND"
    SNAPSHOT_NOT_FOUND = "SNAPSHOT_NOT_FOUND"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    MISSING_COMPANY_ID = "MISSING_COMPANY_ID"
    CONFLICTING_OPTIONS = "CONFLICTING_OPTIONS"
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    SELF_MERGE = "SELF_MERGE"
    BASE_RESUME_MISSING = "BASE_RESUME_MISSING"
    RESUME_NOT_FOUND = "RESUME_NOT_FOUND"
    RANK_RESULT_NOT_FOUND = "RANK_RESULT_NOT_FOUND"
    RANKING_MOVED_TO_SKILL = "RANKING_MOVED_TO_SKILL"
    PREP_SESSION_NOT_FOUND = "PREP_SESSION_NOT_FOUND"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    QUESTION_NOT_FOUND = "QUESTION_NOT_FOUND"

    @property
    def status(self) -> int:
        return _STATUS[self]


_STATUS: dict[ErrorCode, int] = {
    ErrorCode.JOB_NOT_FOUND: 404,
    ErrorCode.NOTE_NOT_FOUND: 404,
    ErrorCode.SNAPSHOT_NOT_FOUND: 404,
    ErrorCode.INVALID_TRANSITION: 422,
    ErrorCode.MISSING_COMPANY_ID: 422,
    ErrorCode.CONFLICTING_OPTIONS: 422,
    ErrorCode.COMPANY_NOT_FOUND: 404,
    ErrorCode.SELF_MERGE: 422,
    ErrorCode.BASE_RESUME_MISSING: 404,
    ErrorCode.RESUME_NOT_FOUND: 404,
    ErrorCode.RANK_RESULT_NOT_FOUND: 404,
    ErrorCode.RANKING_MOVED_TO_SKILL: 501,
    ErrorCode.PREP_SESSION_NOT_FOUND: 404,
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.QUESTION_NOT_FOUND: 404,
}


class BusinessError(BaseModel):
    """A business-rule failure. Branch on `code`; `detail` is for humans and may change.

    Input-validation failures use the separate HTTPValidationError shape (list-valued
    `detail`, no `code`); a 422 with a `code` key is always a business error.
    """

    detail: str
    code: ErrorCode


class ApiError(Exception):
    """Raise from a route to return a BusinessError body with the code's HTTP status."""

    def __init__(self, code: ErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return JSONResponse(
        status_code=exc.code.status,
        content={"detail": exc.detail, "code": exc.code.value},
    )


def _ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{name}"}


def error_responses(*codes: ErrorCode) -> dict[int | str, dict[str, Any]]:
    """Build a route's ``responses=`` entries for the business errors it can raise."""
    by_status: dict[int, list[ErrorCode]] = defaultdict(list)
    for code in codes:
        by_status[code.status].append(code)

    responses: dict[int | str, dict[str, Any]] = {}
    for status, grouped in sorted(by_status.items()):
        description = "Business error. code: " + " | ".join(c.value for c in grouped)
        if status == 422:
            # A custom 422 replaces FastAPI's default validation 422, so document both.
            description += ". Input-validation errors use HTTPValidationError (no code)."
            schema = {"anyOf": [_ref("BusinessError"), _ref("HTTPValidationError")]}
            # No "model" here: FastAPI would merge it in as a sibling $ref. BusinessError
            # is still registered as a component through the other statuses' "model".
            responses[status] = {
                "description": description,
                "content": {"application/json": {"schema": schema}},
            }
        else:
            responses[status] = {"model": BusinessError, "description": description}
    return responses
