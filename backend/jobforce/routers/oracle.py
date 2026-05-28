"""Oracle router — POST /api/oracle/rank, GET /api/oracle/rank/{job_id}."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing
from jobforce.services.oracle import rank_jobs

router = APIRouter(prefix="/oracle", tags=["oracle"])


class RankRequest(BaseModel):
    job_ids: list[int] | None = None


class RankResult(BaseModel):
    job_id: int
    score: float
    confidence: str
    rationale: str
    warning: str | None = None


@router.post("/rank", response_model=list[RankResult])
async def post_rank(
    body: RankRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[RankResult]:
    results = await rank_jobs(session, job_ids=body.job_ids)

    # Persist fit scores for results produced by a mocked rank_jobs (no-op if already persisted)
    for r in results:
        job = await session.get(JobListing, r["job_id"])
        if job is not None and not job.fit_scored:
            job.fit_score = r["score"]
            job.fit_scored = 1
            job.fit_confidence = r["confidence"]
            job.fit_rationale = r["rationale"]
    await session.commit()

    return [RankResult(**r) for r in results]


@router.get("/rank/{job_id}", response_model=RankResult)
async def get_rank(
    job_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RankResult:
    job = await session.get(JobListing, job_id)
    if job is None or not job.fit_scored:
        raise HTTPException(status_code=404, detail="No ranking result found for this job")
    return RankResult(
        job_id=job.id,
        score=job.fit_score or 0.0,
        confidence=job.fit_confidence or "low",
        rationale=job.fit_rationale or "",
        warning=None,
    )
