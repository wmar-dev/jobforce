"""Every business-rule error returns {detail, code}; detail text is unchanged (FR-008a, FR-014)."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, InterviewSession, JobListing

MISSING = 999999
_BASE_RESUME_MISSING = "No base resume found — add config/resume.json"


def _assert_error(resp: Any, status: int, code: str, detail: str | None = None) -> None:
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["code"] == code
    assert isinstance(body["detail"], str)
    if detail is not None:
        assert body["detail"] == detail
    assert set(body) == {"detail", "code"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", f"/api/jobs/{MISSING}"),
        ("PATCH", f"/api/jobs/{MISSING}"),
        ("DELETE", f"/api/jobs/{MISSING}"),
        ("POST", f"/api/jobs/{MISSING}/reparse"),
        ("GET", f"/api/jobs/{MISSING}/note"),
        ("DELETE", f"/api/jobs/{MISSING}/note"),
        ("GET", f"/api/coach/jobs/{MISSING}/latest-session"),
    ],
)
async def test_job_not_found(test_client: AsyncClient, method: str, path: str) -> None:
    kwargs: dict[str, Any] = {"json": {}} if method == "PATCH" else {}
    resp = await test_client.request(method, path, **kwargs)
    _assert_error(resp, 404, "JOB_NOT_FOUND", "Job listing not found")


async def test_job_not_found_on_body_routes(test_client: AsyncClient) -> None:
    resp = await test_client.patch(f"/api/jobs/{MISSING}/status", json={"status": "applied"})
    _assert_error(resp, 404, "JOB_NOT_FOUND", "Job listing not found")
    resp = await test_client.put(f"/api/jobs/{MISSING}/note", json={"body": "x"})
    _assert_error(resp, 404, "JOB_NOT_FOUND", "Job listing not found")
    resp = await test_client.post("/api/coach/prep", json={"job_id": MISSING, "questions": []})
    _assert_error(resp, 404, "JOB_NOT_FOUND", "Job listing not found")
    await test_client.put("/api/resume/base", json={"personal_info": {"name": "A"}})
    resp = await test_client.post(
        "/api/resume/tailor", json={"job_id": MISSING, "structured_data": {}}
    )
    _assert_error(resp, 404, "JOB_NOT_FOUND", "Job listing not found")


async def test_note_not_found(test_client: AsyncClient, sample_job: JobListing) -> None:
    resp = await test_client.get(f"/api/jobs/{sample_job.id}/note")
    _assert_error(resp, 404, "NOTE_NOT_FOUND", "Note not found")
    resp = await test_client.delete(f"/api/jobs/{sample_job.id}/note")
    _assert_error(resp, 404, "NOTE_NOT_FOUND", "Note not found")


async def test_snapshot_not_found(test_client: AsyncClient, sample_job: JobListing) -> None:
    resp = await test_client.post(f"/api/jobs/{sample_job.id}/reparse")
    _assert_error(resp, 404, "SNAPSHOT_NOT_FOUND", "No HTML snapshot stored for this job")


async def test_invalid_transition(test_client: AsyncClient, sample_job: JobListing) -> None:
    resp = await test_client.patch(f"/api/jobs/{sample_job.id}/status", json={"status": "offer"})
    _assert_error(resp, 422, "INVALID_TRANSITION", "Invalid transition: saved → offer")


async def test_bulk_archive_option_errors(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/jobs/bulk-archive?all_active=true")
    _assert_error(resp, 422, "MISSING_COMPANY_ID", "all_active/saved_only requires company_id")
    resp = await test_client.post(
        "/api/jobs/bulk-archive?all_active=true&saved_only=true&company_id=1"
    )
    _assert_error(
        resp, 422, "CONFLICTING_OPTIONS", "all_active and saved_only are mutually exclusive"
    )


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("PATCH", f"/api/companies/{MISSING}", {}),
        ("GET", f"/api/companies/{MISSING}", None),
        ("POST", f"/api/companies/{MISSING}/merge", {"source_id": 1}),
        ("POST", f"/api/companies/{MISSING}/notes", {"content": "x"}),
        ("GET", f"/api/companies/{MISSING}/notes", None),
    ],
)
async def test_company_not_found(
    test_client: AsyncClient, method: str, path: str, body: dict[str, Any] | None
) -> None:
    resp = await test_client.request(method, path, json=body)
    _assert_error(resp, 404, "COMPANY_NOT_FOUND", "Company not found")


async def test_self_merge(test_client: AsyncClient, sample_company: Company) -> None:
    resp = await test_client.post(
        f"/api/companies/{sample_company.id}/merge", json={"source_id": sample_company.id}
    )
    _assert_error(resp, 422, "SELF_MERGE", "Cannot merge a company into itself")


async def test_base_resume_missing(test_client: AsyncClient, sample_job: JobListing) -> None:
    resp = await test_client.get("/api/resume/base")
    _assert_error(resp, 404, "BASE_RESUME_MISSING", _BASE_RESUME_MISSING)
    resp = await test_client.post(
        "/api/resume/tailor", json={"job_id": sample_job.id, "structured_data": {}}
    )
    _assert_error(resp, 404, "BASE_RESUME_MISSING", _BASE_RESUME_MISSING)
    resp = await test_client.post("/api/resume/0/export")
    _assert_error(resp, 404, "BASE_RESUME_MISSING", _BASE_RESUME_MISSING)


async def test_resume_not_found(test_client: AsyncClient) -> None:
    resp = await test_client.post(f"/api/resume/{MISSING}/export")
    _assert_error(resp, 404, "RESUME_NOT_FOUND", "Resume not found")


async def test_rank_result_not_found(test_client: AsyncClient) -> None:
    resp = await test_client.get(f"/api/oracle/rank/{MISSING}")
    _assert_error(resp, 404, "RANK_RESULT_NOT_FOUND", "No ranking result found for this job")


async def test_ranking_moved_to_skill(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/oracle/rank", json={})
    _assert_error(resp, 501, "RANKING_MOVED_TO_SKILL")
    assert "/oracle-rank" in resp.json()["detail"]


async def test_prep_session_not_found(test_client: AsyncClient, sample_job: JobListing) -> None:
    resp = await test_client.get(f"/api/coach/jobs/{sample_job.id}/latest-session")
    _assert_error(resp, 404, "PREP_SESSION_NOT_FOUND", "No prep session found for this job")


async def test_session_not_found(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        f"/api/coach/sessions/{MISSING}/answer", json={"question_id": "q1", "answer": "a"}
    )
    _assert_error(resp, 404, "SESSION_NOT_FOUND", f"Interview session {MISSING} not found")
    resp = await test_client.get(f"/api/coach/sessions/{MISSING}/summary")
    _assert_error(resp, 404, "SESSION_NOT_FOUND", f"Interview session {MISSING} not found")


async def test_question_not_found(
    test_client: AsyncClient, db_session: AsyncSession, sample_job: JobListing
) -> None:
    interview = InterviewSession(job_listing_id=sample_job.id, questions="[]")
    db_session.add(interview)
    await db_session.commit()
    await db_session.refresh(interview)
    resp = await test_client.post(
        f"/api/coach/sessions/{interview.id}/answer", json={"question_id": "nope", "answer": "a"}
    )
    _assert_error(
        resp, 404, "QUESTION_NOT_FOUND", f"Question nope not found in session {interview.id}"
    )


async def test_validation_errors_keep_list_detail_and_no_code(test_client: AsyncClient) -> None:
    resp = await test_client.patch("/api/jobs/abc", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert isinstance(body["detail"], list)
    assert "code" not in body
