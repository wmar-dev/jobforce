"""Coach service — store and retrieve interview prep sessions."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import InterviewSession

logger = logging.getLogger(__name__)


async def store_prep_pack(
    session: AsyncSession,
    job_id: int,
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persist a pre-formed question list as an InterviewSession."""
    interview = InterviewSession(
        job_listing_id=job_id,
        session_type="prep",
        questions=json.dumps(questions),
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)
    return {
        "session_id": interview.id,
        "job_id": job_id,
        "questions": questions,
    }


async def evaluate_answer(
    session: AsyncSession,
    session_id: int,
    question_id: str,
    answer: str,  # noqa: ARG001
) -> dict[str, Any]:
    """Stub — answer evaluation via AI is out of scope post-migration."""
    interview = await session.get(InterviewSession, session_id)
    if interview is None:
        raise ValueError(f"Interview session {session_id} not found")

    questions: list[dict[str, Any]] = json.loads(interview.questions)
    if not any(q.get("id") == question_id for q in questions):
        raise ValueError(f"Question {question_id} not found in session {session_id}")

    return {
        "question_id": question_id,
        "feedback": "Submit answers via mock interview mode.",
        "score": 0.0,
    }


async def get_session_summary_data(
    session: AsyncSession,
    session_id: int,
) -> dict[str, Any]:
    """Return overall session summary."""
    interview = await session.get(InterviewSession, session_id)
    if interview is None:
        raise ValueError(f"Interview session {session_id} not found")

    summary_text = interview.overall_summary or ""

    if summary_text:
        try:
            result: dict[str, Any] = json.loads(summary_text)
            return result
        except (json.JSONDecodeError, ValueError):
            pass

    return {
        "session_id": session_id,
        "overall_score": 0.0,
        "summary": "No answers submitted yet.",
        "areas_to_improve": [],
    }
