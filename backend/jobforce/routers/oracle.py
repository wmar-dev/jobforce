"""Oracle router — GET /api/oracle/rank/{job_id}.

Job fit ranking is now performed by Claude Code via the /oracle-rank skill.
POST /api/oracle/rank returns 501 to guide callers to the new workflow.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing
from jobforce.routers.errors import ApiError, ErrorCode, error_responses
from jobforce.routers.resume_schema import FitConfidenceStr

router = APIRouter(prefix="/oracle", tags=["oracle"])


class RankRequest(BaseModel):
    job_ids: list[int] | None = None


class RankResult(BaseModel):
    job_id: int
    score: float
    confidence: FitConfidenceStr
    rationale: str
    warning: str | None = None


@router.post(
    "/rank",
    response_model=None,
    status_code=501,
    summary="Removed: run the /oracle-rank skill instead",
    deprecated=True,
    responses=error_responses(ErrorCode.RANKING_MOVED_TO_SKILL),
)
async def post_rank(body: RankRequest) -> None:
    """Always returns RANKING_MOVED_TO_SKILL (501). Ranking runs in Claude Code via
    /oracle-rank, which writes scores with `PATCH /jobs/{job_id}`."""
    raise ApiError(
        ErrorCode.RANKING_MOVED_TO_SKILL,
        "Oracle ranking is now performed via Claude Code. "
        "Run /oracle-rank in Claude Code to score jobs.",
    )


@router.get(
    "/rank/{job_id}",
    response_model=RankResult,
    summary="Get a job's Oracle fit score",
    responses=error_responses(ErrorCode.RANK_RESULT_NOT_FOUND),
)
async def get_rank(
    job_id: Annotated[int, Path(description="Job listing id")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RankResult:
    """Return the score and rationale; RANK_RESULT_NOT_FOUND if the job is missing or
    has not been scored yet."""
    job = await session.get(JobListing, job_id)
    if job is None or not job.fit_scored:
        raise ApiError(ErrorCode.RANK_RESULT_NOT_FOUND, "No ranking result found for this job")
    return RankResult(
        job_id=job.id,
        score=job.fit_score or 0.0,
        confidence=job.fit_confidence or "low",
        rationale=job.fit_rationale or "",
        warning=None,
    )
