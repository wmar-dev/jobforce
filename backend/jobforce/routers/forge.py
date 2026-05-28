"""Forge router — resume CRUD, tailor, and PDF export."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing, Resume
from jobforce.services.forge import render_pdf, tailor_resume

router = APIRouter(prefix="/resume", tags=["forge"])


class ResumeDiffItem(BaseModel):
    field: str
    original: str
    tailored: str


class ResumeOut(BaseModel):
    id: int
    label: str
    is_base: bool
    job_listing_id: int | None
    structured_data: Any
    created_at: str
    updated_at: str


class TailoredResumeOut(ResumeOut):
    diff: list[ResumeDiffItem]


class TailorRequest(BaseModel):
    job_id: int
    base_resume_id: int


def _to_out(resume: Resume) -> ResumeOut:
    return ResumeOut(
        id=resume.id,
        label=resume.label,
        is_base=bool(resume.is_base),
        job_listing_id=resume.job_listing_id,
        structured_data=json.loads(resume.structured_data),
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


@router.get("/base", response_model=ResumeOut)
async def get_base_resume(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResumeOut:
    result = await session.execute(select(Resume).where(Resume.is_base == 1).limit(1))
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=404, detail="No base resume found")
    return _to_out(resume)


@router.put("/base", response_model=ResumeOut)
async def put_base_resume(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResumeOut:
    body = await request.json()
    result = await session.execute(select(Resume).where(Resume.is_base == 1).limit(1))
    resume = result.scalar_one_or_none()

    structured_json = json.dumps(body if isinstance(body, dict) else body)

    if resume is None:
        resume = Resume(
            label="Base Resume",
            is_base=1,
            structured_data=structured_json,
        )
        session.add(resume)
    else:
        resume.structured_data = structured_json

    await session.commit()
    await session.refresh(resume)
    return _to_out(resume)


@router.post("/tailor", response_model=TailoredResumeOut)
async def post_tailor(
    body: TailorRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TailoredResumeOut:
    job = await session.get(JobListing, body.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job listing not found")

    base_resume = await session.get(Resume, body.base_resume_id)
    if base_resume is None:
        raise HTTPException(status_code=404, detail="Base resume not found")

    try:
        result = await tailor_resume(session, body.base_resume_id, body.job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    tailored_data = result["structured_data"]
    diff_raw = result["diff"]

    tailored_resume = Resume(
        label=f"Tailored for {job.title}",
        is_base=0,
        job_listing_id=body.job_id,
        structured_data=json.dumps(tailored_data),
    )
    session.add(tailored_resume)
    await session.commit()
    await session.refresh(tailored_resume)

    return TailoredResumeOut(
        **_to_out(tailored_resume).model_dump(),
        diff=[ResumeDiffItem(**d) for d in diff_raw],
    )


@router.post("/{resume_id}/export")
async def export_resume_pdf(
    resume_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    resume = await session.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    structured_data = json.loads(resume.structured_data)

    try:
        pdf_bytes = await render_pdf(structured_data)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc), "code": "LATEX_UNAVAILABLE"},
        )

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{resume_id}.pdf"'},
    )
