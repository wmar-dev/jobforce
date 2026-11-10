from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jobforce.db.engine import get_session
from jobforce.db.models import Company, JobListing, MeetingNote
from jobforce.db.models import _now as _db_now
from jobforce.routers.errors import ApiError, ErrorCode, error_responses
from jobforce.routers.resume_schema import (
    PIPELINE_STATUSES,
    ROLE_TYPES,
    OptionalFitConfidenceStr,
    OptionalPipelineStatusStr,
    OptionalRoleTypeStr,
    PipelineStatusStr,
)
from jobforce.services.parse import parse_html
from jobforce.services.scout import bulk_archive_low_score, transition_status
from jobforce.services.storage import retrieve_snapshot

router = APIRouter(tags=["jobs"])

JobId = Annotated[int, Path(description="Job listing id")]
_JOB_404 = error_responses(ErrorCode.JOB_NOT_FOUND)


class CompanyRef(BaseModel):
    id: int
    name: str


class StatusTransitionOut(BaseModel):
    """One audited pipeline move."""

    id: int
    from_status: OptionalPipelineStatusStr = Field(description="Null for the initial capture")
    to_status: PipelineStatusStr
    transitioned_at: str


class JobListingOut(BaseModel):
    """A captured job listing as shown in lists."""

    id: int
    title: str
    company: CompanyRef
    location: str | None
    role_type: OptionalRoleTypeStr
    posted_at: str | None
    source_url: str
    status: PipelineStatusStr
    fit_scored: bool = Field(description="True once /oracle-rank has scored this job")
    fit_score: float | None = Field(description="0.0–1.0 fit score written by /oracle-rank")
    fit_confidence: OptionalFitConfidenceStr
    crawled_at: str | None
    created_at: str
    has_note: bool = Field(False, description="True if a per-job note exists")


class JobListingDetail(JobListingOut):
    description: str | None
    fit_rationale: str | None
    status_history: list[StatusTransitionOut]


class JobListPage(BaseModel):
    total: int
    items: list[JobListingOut]


class JobPatchRequest(BaseModel):
    # extra="forbid" so a "status" field (handled by PATCH /jobs/{id}/status,
    # which records a status_transitions row) errors loudly instead of being
    # silently dropped.
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    location: str | None = None
    role_type: OptionalRoleTypeStr = None
    posted_at: str | None = None
    description: str | None = None
    fit_score: float | None = None
    fit_scored: int | None = None
    fit_confidence: OptionalFitConfidenceStr = None
    fit_rationale: str | None = None


class StatusPatchRequest(BaseModel):
    status: PipelineStatusStr = Field(description="Target status; must be a valid transition")


class StatusPatchResponse(BaseModel):
    id: int
    status: PipelineStatusStr
    transitioned_at: str


class BulkArchiveResult(BaseModel):
    archived_count: int = Field(description="Number of jobs moved to archived")


class JobNoteOut(BaseModel):
    id: int
    job_listing_id: int
    body: str
    created_at: str
    updated_at: str


class JobNoteUpsert(BaseModel):
    body: str


def _to_out(job: JobListing, *, has_note: bool = False) -> JobListingOut:
    return JobListingOut(
        id=job.id,
        title=job.title,
        company=CompanyRef(id=job.company.id, name=job.company.name),
        location=job.location,
        role_type=job.role_type,
        posted_at=job.posted_at,
        source_url=job.source_url,
        status=job.status,
        fit_scored=bool(job.fit_scored),
        fit_score=job.fit_score,
        fit_confidence=job.fit_confidence,
        crawled_at=job.crawled_at,
        created_at=job.created_at,
        has_note=has_note,
    )


def _apply_default_status_filter(
    stmt: Select[tuple[JobListing]], status: str | None, source_url: str | None
) -> Select[tuple[JobListing]]:
    """Apply the status filter, or the default archived/withdrawn/rejected exclusion.

    Skipped entirely when filtering by source_url, since duplicate lookups must
    match regardless of pipeline status.
    """
    if status:
        return stmt.where(JobListing.status == status)
    if source_url:
        return stmt
    return stmt.where(JobListing.status.notin_(["archived", "withdrawn", "rejected"]))


def _apply_company_filter(
    stmt: Select[tuple[JobListing]], company: str | None, sort_by: str
) -> Select[tuple[JobListing]]:
    """Join Company when filtering or sorting by it; filter by name substring."""
    if company:
        return stmt.join(Company, JobListing.company_id == Company.id).where(
            Company.name.ilike(f"%{company}%")
        )
    if sort_by == "company":
        return stmt.join(Company, JobListing.company_id == Company.id)
    return stmt


def _apply_field_filters(
    stmt: Select[tuple[JobListing]],
    *,
    fit_scored: bool | None,
    min_score: float | None,
    location: str | None,
    role_type: str | None,
    title: str | None,
    q: str | None,
    posted_after: str | None,
) -> Select[tuple[JobListing]]:
    if fit_scored is not None:
        stmt = stmt.where(JobListing.fit_scored == (1 if fit_scored else 0))
    if min_score is not None:
        stmt = stmt.where(JobListing.fit_score >= min_score)
    if location:
        stmt = stmt.where(JobListing.location.ilike(f"%{location}%"))
    if role_type:
        stmt = stmt.where(JobListing.role_type == role_type)
    if title:
        stmt = stmt.where(JobListing.title.ilike(f"%{title}%"))
    if q:
        stmt = stmt.where(JobListing.description.ilike(f"%{q}%"))
    if posted_after:
        stmt = stmt.where(JobListing.posted_at >= posted_after)
    return stmt


_SORT_COLUMNS: dict[str, Any] = {
    "fit_score": JobListing.fit_score,
    "created_at": JobListing.created_at,
    "posted_at": JobListing.posted_at,
    "title": JobListing.title,
    "status": JobListing.status,
    "company": Company.name,
}


@router.get("/jobs", response_model=JobListPage, summary="List and filter job listings")
async def get_jobs(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = Query(
        None,
        description=(
            f"Only jobs in this status ({', '.join(PIPELINE_STATUSES)}). When omitted, "
            "archived/withdrawn/rejected jobs are excluded (unless source_url is given)."
        ),
    ),
    company_id: int | None = Query(None, description="Exact company id"),
    company: str | None = Query(
        None, description="Case-insensitive substring match on company name"
    ),
    fit_scored: bool | None = Query(None, description="Filter on whether Oracle has scored it"),
    min_score: float | None = Query(None, description="Minimum fit_score (0.0–1.0)"),
    location: str | None = Query(None, description="Case-insensitive substring match on location"),
    role_type: str | None = Query(None, description=f"Exact role type ({', '.join(ROLE_TYPES)})"),
    source_url: str | None = Query(
        None,
        description=(
            "Exact-match lookup by posting URL, to check whether a job is already "
            "captured. Matches regardless of pipeline status."
        ),
    ),
    title: str | None = Query(None, description="Case-insensitive substring match on title"),
    q: str | None = Query(None, description="Case-insensitive substring match on description"),
    posted_after: str | None = Query(
        None, description="Only jobs posted on/after this ISO date (YYYY-MM-DD)"
    ),
    sort_by: str = Query(
        "fit_score",
        pattern="^(fit_score|created_at|posted_at|title|status|company)$",
        description="Sort column; ties break on created_at desc for stable paging",
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$", description="asc or desc"),
    limit: int = Query(50, ge=1, le=200, description="Page size (1–200)"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
) -> JobListPage:
    """Return one page of job listings plus the total match count.

    All text filters are case-insensitive substring matches unless noted. Nulls sort
    last in either direction.
    """
    stmt = select(JobListing).options(selectinload(JobListing.company))
    stmt = _apply_default_status_filter(stmt, status, source_url)
    if source_url:
        stmt = stmt.where(JobListing.source_url == source_url)
    if company_id:
        stmt = stmt.where(JobListing.company_id == company_id)
    stmt = _apply_company_filter(stmt, company, sort_by)
    stmt = _apply_field_filters(
        stmt,
        fit_scored=fit_scored,
        min_score=min_score,
        location=location,
        role_type=role_type,
        title=title,
        q=q,
        posted_after=posted_after,
    )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    col = _SORT_COLUMNS[sort_by]
    primary_order = col.desc().nulls_last() if sort_dir == "desc" else col.asc().nulls_last()
    # Always break ties by created_at desc so order is stable across pages.
    stmt = stmt.order_by(primary_order, JobListing.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    jobs = result.scalars().all()

    # Fetch which job IDs have a note in one query.
    if jobs:
        job_ids = [j.id for j in jobs]
        note_stmt = select(MeetingNote.job_listing_id).where(
            MeetingNote.job_listing_id.in_(job_ids)
        )
        note_result = await session.execute(note_stmt)
        jobs_with_note: set[int] = {row[0] for row in note_result.all()}
    else:
        jobs_with_note = set()

    return JobListPage(
        total=total,
        items=[_to_out(j, has_note=j.id in jobs_with_note) for j in jobs],
    )


@router.post(
    "/jobs/bulk-archive",
    response_model=BulkArchiveResult,
    summary="Archive many jobs at once",
    responses=error_responses(ErrorCode.MISSING_COMPANY_ID, ErrorCode.CONFLICTING_OPTIONS),
)
async def bulk_archive_jobs(
    session: Annotated[AsyncSession, Depends(get_session)],
    company_id: int | None = Query(
        None, description="Limit to one company; required with all_active or saved_only"
    ),
    all_active: bool = Query(
        False,
        description=(
            "Archive every saved/shortlisted job for company_id regardless of fit "
            "score, instead of only low-score (<0.50) saved jobs. Requires company_id."
        ),
    ),
    saved_only: bool = Query(
        False,
        description=(
            "Archive every saved job for company_id regardless of fit score, "
            "leaving shortlisted jobs untouched. Requires company_id."
        ),
    ),
) -> BulkArchiveResult:
    """Archive jobs in one of three modes.

    - Default: `saved` jobs with `fit_score < 0.50` (optionally for one company);
      shortlisted, unscored and in-pipeline jobs are skipped.
    - `all_active=true`: every `saved`/`shortlisted` job for `company_id`.
    - `saved_only=true`: every `saved` job for `company_id`, any score.

    `all_active` and `saved_only` require `company_id` and are mutually exclusive.
    """
    if (all_active or saved_only) and company_id is None:
        raise ApiError(ErrorCode.MISSING_COMPANY_ID, "all_active/saved_only requires company_id")
    if all_active and saved_only:
        raise ApiError(
            ErrorCode.CONFLICTING_OPTIONS, "all_active and saved_only are mutually exclusive"
        )
    count = await bulk_archive_low_score(
        session, company_id=company_id, all_active=all_active, saved_only=saved_only
    )
    return BulkArchiveResult(archived_count=count)


@router.get(
    "/jobs/{job_id}",
    response_model=JobListingDetail,
    summary="Get one job with description and status history",
    responses=_JOB_404,
)
async def get_job(
    job_id: JobId,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobListingDetail:
    """Return the full listing, including description, Oracle rationale, and the
    status history in chronological order."""
    result = await session.execute(
        select(JobListing)
        .options(
            selectinload(JobListing.company),
            selectinload(JobListing.status_transitions),
        )
        .where(JobListing.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")

    transitions = sorted(job.status_transitions, key=lambda t: t.transitioned_at)
    return JobListingDetail(
        **_to_out(job).model_dump(),
        description=job.description,
        fit_rationale=job.fit_rationale,
        status_history=[
            StatusTransitionOut(
                id=t.id,
                from_status=t.from_status,
                to_status=t.to_status,
                transitioned_at=t.transitioned_at,
            )
            for t in transitions
        ],
    )


@router.patch(
    "/jobs/{job_id}",
    response_model=JobListingDetail,
    summary="Update job fields (not status)",
    responses=_JOB_404,
)
async def patch_job(
    job_id: JobId,
    body: JobPatchRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Any:
    """Set any of the given fields; omitted or null fields are left unchanged.

    Used by /oracle-rank to write fit scores. A `status` field is rejected (422):
    use `PATCH /jobs/{job_id}/status` so the move is validated and audited.
    """
    result = await session.execute(
        select(JobListing)
        .options(
            selectinload(JobListing.company),
            selectinload(JobListing.status_transitions),
        )
        .where(JobListing.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(job, field, value)
    await session.commit()
    await session.refresh(job)
    transitions = sorted(job.status_transitions, key=lambda t: t.transitioned_at)
    return JobListingDetail(
        **_to_out(job).model_dump(),
        description=job.description,
        fit_rationale=job.fit_rationale,
        status_history=[
            StatusTransitionOut(
                id=t.id,
                from_status=t.from_status,
                to_status=t.to_status,
                transitioned_at=t.transitioned_at,
            )
            for t in transitions
        ],
    )


@router.delete(
    "/jobs/{job_id}", status_code=204, summary="Delete a job listing", responses=_JOB_404
)
async def delete_job(
    job_id: JobId,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Permanently delete the listing and its dependent rows. Prefer archiving."""
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    await session.delete(job)
    await session.commit()


@router.post(
    "/jobs/{job_id}/reparse",
    response_model=JobListingDetail,
    summary="Re-extract fields from the stored HTML snapshot",
    responses=error_responses(ErrorCode.JOB_NOT_FOUND, ErrorCode.SNAPSHOT_NOT_FOUND),
)
async def reparse_job(
    job_id: JobId,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Any:
    """Re-extract fields from the stored HTML snapshot using the current site adapter.

    Use this after improving a site adapter in `services/parse/sites/` to update
    title, location, role_type, and description without re-crawling the page.
    Returns 404 if the job or its snapshot does not exist.
    """
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    html_bytes = await retrieve_snapshot(session, job_id)
    if not html_bytes:
        raise ApiError(ErrorCode.SNAPSHOT_NOT_FOUND, "No HTML snapshot stored for this job")
    parsed = parse_html(html_bytes.decode("utf-8", errors="replace"), job.source_url)
    for field in ("title", "location", "role_type", "description", "posted_at"):
        v = parsed.get(field)
        if v is not None:
            setattr(job, field, v)
    # role_type is a classification, not an extraction: None means "no longer
    # detected", so clear a stale value (e.g. a since-fixed misclassification)
    if parsed.get("role_type") is None:
        job.role_type = None
    await session.commit()
    await session.refresh(job)
    return await get_job(job_id, session)


@router.patch(
    "/jobs/{job_id}/status",
    response_model=StatusPatchResponse,
    summary="Move a job to a new pipeline status",
    responses=error_responses(ErrorCode.JOB_NOT_FOUND, ErrorCode.INVALID_TRANSITION),
)
async def patch_job_status(
    job_id: JobId,
    body: StatusPatchRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Any:
    """The only way to change `status`. Validates the move against the pipeline
    state machine and records a status_transitions row. Disallowed moves (e.g.
    saved → offer, or anything out of a terminal status) return INVALID_TRANSITION."""
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    try:
        result = await transition_status(session, job_id, body.status)
    except ValueError as exc:
        raise ApiError(ErrorCode.INVALID_TRANSITION, str(exc)) from exc
    return StatusPatchResponse(**result)


async def _get_job_note(job_id: int, session: AsyncSession) -> MeetingNote | None:
    result = await session.execute(select(MeetingNote).where(MeetingNote.job_listing_id == job_id))
    return result.scalar_one_or_none()


_JOB_OR_NOTE_404 = error_responses(ErrorCode.JOB_NOT_FOUND, ErrorCode.NOTE_NOT_FOUND)


@router.get(
    "/jobs/{job_id}/note",
    response_model=JobNoteOut,
    summary="Get the job's note",
    responses=_JOB_OR_NOTE_404,
)
async def get_job_note(
    job_id: JobId,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobNoteOut:
    """Return the single free-text note attached to this job."""
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    note = await _get_job_note(job_id, session)
    if note is None:
        raise ApiError(ErrorCode.NOTE_NOT_FOUND, "Note not found")
    return JobNoteOut(
        id=note.id,
        job_listing_id=job_id,
        body=note.body,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.put(
    "/jobs/{job_id}/note",
    response_model=JobNoteOut,
    summary="Create or replace the job's note",
    responses=_JOB_404,
)
async def upsert_job_note(
    job_id: JobId,
    body: JobNoteUpsert,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobNoteOut:
    """Create the note if missing, otherwise replace its body."""
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    note = await _get_job_note(job_id, session)
    now = _db_now()
    if note is None:
        note = MeetingNote(
            company_id=job.company_id,
            job_listing_id=job_id,
            body=body.body,
            created_at=now,
            updated_at=now,
        )
        session.add(note)
    else:
        note.body = body.body
        note.updated_at = now
    await session.commit()
    await session.refresh(note)
    return JobNoteOut(
        id=note.id,
        job_listing_id=job_id,
        body=note.body,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.delete(
    "/jobs/{job_id}/note",
    status_code=204,
    summary="Delete the job's note",
    responses=_JOB_OR_NOTE_404,
)
async def delete_job_note(
    job_id: JobId,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove the note attached to this job."""
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ApiError(ErrorCode.JOB_NOT_FOUND, "Job listing not found")
    note = await _get_job_note(job_id, session)
    if note is None:
        raise ApiError(ErrorCode.NOTE_NOT_FOUND, "Note not found")
    await session.delete(note)
    await session.commit()
