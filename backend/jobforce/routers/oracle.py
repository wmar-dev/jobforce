"""Oracle router — GET /api/oracle/rank/{job_id}.

Job fit ranking is now performed by Claude Code via the /oracle-rank skill.
POST /api/oracle/rank returns 501 to guide callers to the new workflow.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing

router = APIRouter(prefix="/oracle", tags=["oracle"])


class RankRequest(BaseModel):
    job_ids: list[int] | None = None


class RankResult(BaseModel):
    job_id: int
    score: float
    confidence: str
    rationale: str
    warning: str | None = None


@router.post("/rank")
async def post_rank(body: RankRequest) -> Any:
    return JSONResponse(
        status_code=501,
        content={
            "detail": (
                "Oracle ranking is now performed via Claude Code. "
                "Run /oracle-rank in Claude Code to score jobs."
            )
        },
    )


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
