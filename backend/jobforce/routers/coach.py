"""Coach router — interview prep and mock interview sessions."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing
from jobforce.services.coach import (
    evaluate_answer,
    generate_prep_pack,
    get_session_summary_data,
)

router = APIRouter(prefix="/coach", tags=["coach"])


class PrepRequest(BaseModel):
    job_id: int


class QuestionOut(BaseModel):
    id: str
    category: str
    text: str
    source_url: str | None = None
    leetcode_url: str | None = None
    guidance: str | None = None


class PrepSessionOut(BaseModel):
    session_id: int
    job_id: int
    questions: list[QuestionOut]


class AnswerRequest(BaseModel):
    question_id: str
    answer: str


class AnswerFeedbackOut(BaseModel):
    question_id: str
    feedback: str
    score: float


class SessionSummaryOut(BaseModel):
    session_id: int
    overall_score: float
    summary: str
    areas_to_improve: list[str]


@router.post("/prep", response_model=PrepSessionOut)
async def post_prep(
    body: PrepRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PrepSessionOut:
    job = await session.get(JobListing, body.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job listing not found")

    try:
        result = await generate_prep_pack(session, body.job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PrepSessionOut(
        session_id=result["session_id"],
        job_id=result["job_id"],
        questions=[QuestionOut(**q) for q in result["questions"]],
    )


@router.post("/sessions/{session_id}/answer", response_model=AnswerFeedbackOut)
async def post_answer(
    session_id: int,
    body: AnswerRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnswerFeedbackOut:
    try:
        result = await evaluate_answer(session, session_id, body.question_id, body.answer)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AnswerFeedbackOut(**result)


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryOut)
async def get_summary(
    session_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SessionSummaryOut:
    try:
        result = await get_session_summary_data(session, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SessionSummaryOut(
        session_id=result["session_id"],
        overall_score=result["overall_score"],
        summary=result["summary"],
        areas_to_improve=result["areas_to_improve"],
    )
