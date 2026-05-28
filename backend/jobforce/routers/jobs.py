from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing
from jobforce.services.scout import transition_status

router = APIRouter(tags=["jobs"])


class CompanyRef(BaseModel):
    id: int
    name: str


class StatusTransitionOut(BaseModel):
    id: int
    from_status: str | None
    to_status: str
    transitioned_at: str


class JobListingOut(BaseModel):
    id: int
    title: str
    company: CompanyRef
    location: str | None
    role_type: str | None
    source_url: str
    status: str
    fit_scored: bool
    fit_score: float | None
    fit_confidence: str | None
    crawled_at: str | None
    created_at: str


class JobListingDetail(JobListingOut):
    description: str | None
    fit_rationale: str | None
    status_history: list[StatusTransitionOut]


class JobListPage(BaseModel):
    total: int
    items: list[JobListingOut]


class JobPatchRequest(BaseModel):
    title: str | None = None
    location: str | None = None
    role_type: str | None = None
    description: str | None = None
    fit_score: float | None = None
    fit_scored: int | None = None
    fit_confidence: str | None = None
    fit_rationale: str | None = None


class StatusPatchRequest(BaseModel):
    status: str


class StatusPatchResponse(BaseModel):
    id: int
    status: str
    transitioned_at: str


def _to_out(job: JobListing) -> JobListingOut:
    return JobListingOut(
        id=job.id,
        title=job.title,
        company=CompanyRef(id=job.company.id, name=job.company.name),
        location=job.location,
        role_type=job.role_type,
        source_url=job.source_url,
        status=job.status,
        fit_scored=bool(job.fit_scored),
        fit_score=job.fit_score,
        fit_confidence=job.fit_confidence,
        crawled_at=job.crawled_at,
        created_at=job.created_at,
    )


@router.get("/jobs", response_model=JobListPage)
async def get_jobs(
    session: Annotated[AsyncSession, Depends(get_session)],
    status: str | None = Query(None),
    company_id: int | None = Query(None),
    min_score: float | None = Query(None),
    location: str | None = Query(None),
    role_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> JobListPage:
    stmt = select(JobListing).options(selectinload(JobListing.company))
    if status:
        stmt = stmt.where(JobListing.status == status)
    if company_id:
        stmt = stmt.where(JobListing.company_id == company_id)
    if min_score is not None:
        stmt = stmt.where(JobListing.fit_score >= min_score)
    if location:
        stmt = stmt.where(JobListing.location.ilike(f"%{location}%"))
    if role_type:
        stmt = stmt.where(JobListing.role_type == role_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(JobListing.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    jobs = result.scalars().all()

    return JobListPage(total=total, items=[_to_out(j) for j in jobs])


@router.get("/jobs/{job_id}", response_model=JobListingDetail)
async def get_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobListingDetail:
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
        raise HTTPException(status_code=404, detail="Job listing not found")

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


@router.patch("/jobs/{job_id}", response_model=JobListingDetail)
async def patch_job(
    job_id: int,
    body: JobPatchRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Any:
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
        raise HTTPException(status_code=404, detail="Job listing not found")
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


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    job = await session.get(JobListing, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job listing not found")
    await session.delete(job)
    await session.commit()


@router.patch("/jobs/{job_id}/status", response_model=StatusPatchResponse)
async def patch_job_status(
    job_id: int,
    body: StatusPatchRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Any:
    job = await session.get(JobListing, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job listing not found")
    try:
        result = await transition_status(session, job_id, body.status)
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "code": "INVALID_TRANSITION"},
        )
    return StatusPatchResponse(**result)
