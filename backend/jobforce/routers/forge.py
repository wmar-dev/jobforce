"""Forge router — resume CRUD, tailor, and export."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.config import RESUME_FILE
from jobforce.db.engine import get_session
from jobforce.db.models import Company, JobListing, Resume
from jobforce.services.forge import ExportResult, compute_diff, export_resume

_RESUME_FILE = RESUME_FILE

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
    structured_data: Any
    base_resume_id: int | None = None


class ExportOut(BaseModel):
    tex_path: str
    pdf_path: str | None


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


@router.get("/tailored", response_model=TailoredResumeOut | None)
async def get_tailored_resume_for_job(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TailoredResumeOut | None:
    """Return the most recent tailored resume for a job, or null if none exists."""
    result = await session.execute(
        select(Resume)
        .where(Resume.is_base == 0, Resume.job_listing_id == job_id)
        .order_by(Resume.updated_at.desc())
        .limit(1)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        return None
    base_data: dict[str, Any] = (
        json.loads(_RESUME_FILE.read_text()) if _RESUME_FILE.exists() else {}
    )
    tailored_data: dict[str, Any] = json.loads(resume.structured_data)
    diff_raw = compute_diff(base_data, tailored_data)
    return TailoredResumeOut(
        **_to_out(resume).model_dump(),
        diff=[ResumeDiffItem(**d) for d in diff_raw],
    )


@router.get("/base", response_model=ResumeOut)
async def get_base_resume() -> ResumeOut:
    if not _RESUME_FILE.exists():
        raise HTTPException(status_code=404, detail="No base resume found — add config/resume.json")
    structured_data = json.loads(_RESUME_FILE.read_text())
    return ResumeOut(
        id=0,
        label="Base Resume",
        is_base=True,
        job_listing_id=None,
        structured_data=structured_data,
        created_at="",
        updated_at="",
    )


@router.put("/base", response_model=ResumeOut)
async def put_base_resume(request: Request) -> ResumeOut:
    body = await request.json()
    structured_data = body if isinstance(body, dict) else body
    _RESUME_FILE.parent.mkdir(parents=True, exist_ok=True)
    _RESUME_FILE.write_text(json.dumps(structured_data, indent=2, ensure_ascii=False))
    return ResumeOut(
        id=0,
        label="Base Resume",
        is_base=True,
        job_listing_id=None,
        structured_data=structured_data,
        created_at="",
        updated_at="",
    )


@router.post("/tailor", response_model=TailoredResumeOut)
async def post_tailor(
    body: TailorRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TailoredResumeOut:
    """Save a tailored resume produced by the /forge-tailor skill.

    The skill performs AI tailoring and sends the result here.
    This endpoint stores it and returns the diff vs the base resume.
    """
    job = await session.get(JobListing, body.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job listing not found")

    if not _RESUME_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="No base resume found — add config/resume.json",
        )

    base_data: dict[str, Any] = json.loads(_RESUME_FILE.read_text())
    tailored_data: dict[str, Any] = body.structured_data
    diff_raw = compute_diff(base_data, tailored_data)

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


@router.post("/{resume_id}/export", response_model=ExportOut)
async def export_resume_endpoint(
    resume_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExportOut:
    """Write .tex and PDF to output/ and return their paths.

    pdf_path is null when LaTeX is unavailable — this is not an error.
    resume_id=0 refers to the current base resume (config/resume.json).
    """
    job_company = "unknown"
    job_title = "resume"

    if resume_id == 0:
        if not _RESUME_FILE.exists():
            raise HTTPException(
                status_code=404, detail="No base resume found — add config/resume.json"
            )
        resume: Any = SimpleNamespace(structured_data=_RESUME_FILE.read_text())
    else:
        resume = await session.get(Resume, resume_id)
        if resume is None:
            raise HTTPException(status_code=404, detail="Resume not found")
        if resume.job_listing_id:
            job = await session.get(JobListing, resume.job_listing_id)
            if job is not None:
                job_title = job.title or "resume"
                company = await session.get(Company, job.company_id)
                if company is not None:
                    job_company = company.name

    result: ExportResult = await export_resume(resume, job_company, job_title)
    return ExportOut(tex_path=result.tex_path, pdf_path=result.pdf_path)
