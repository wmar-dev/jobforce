"""Dashboard router — GET /api/dashboard."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jobforce.db.engine import get_session
from jobforce.db.models import JobListing, MeetingNote, StatusTransition

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class PipelineCounts(BaseModel):
    saved: int
    shortlisted: int
    applied: int
    interviewing: int
    offer: int
    rejected: int
    withdrawn: int


class RecentTransitionOut(BaseModel):
    job_id: int
    job_title: str
    from_status: str | None
    to_status: str
    transitioned_at: str


class RecentNoteOut(BaseModel):
    id: int
    company_id: int
    content: str
    created_at: str


class DashboardOut(BaseModel):
    counts: PipelineCounts
    recent_transitions: list[RecentTransitionOut]
    recent_notes: list[RecentNoteOut]


@router.get("", response_model=DashboardOut)
async def get_dashboard(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DashboardOut:
    # Pipeline counts per status
    counts: dict[str, int] = {}
    for status in (
        "saved",
        "shortlisted",
        "applied",
        "interviewing",
        "offer",
        "rejected",
        "withdrawn",
    ):
        result = await session.execute(
            select(func.count()).select_from(JobListing).where(JobListing.status == status)
        )
        counts[status] = result.scalar_one()

    # Last 10 status transitions with job info
    trans_result = await session.execute(
        select(StatusTransition)
        .options(selectinload(StatusTransition.job_listing))
        .order_by(StatusTransition.transitioned_at.desc())
        .limit(10)
    )
    transitions = trans_result.scalars().all()

    recent_transitions = [
        RecentTransitionOut(
            job_id=t.job_listing_id,
            job_title=t.job_listing.title if t.job_listing else "",
            from_status=t.from_status,
            to_status=t.to_status,
            transitioned_at=t.transitioned_at,
        )
        for t in transitions
    ]

    # Last 5 meeting notes
    notes_result = await session.execute(
        select(MeetingNote).order_by(MeetingNote.created_at.desc()).limit(5)
    )
    notes = notes_result.scalars().all()

    recent_notes = [
        RecentNoteOut(
            id=n.id,
            company_id=n.company_id,
            content=n.body,
            created_at=n.created_at,
        )
        for n in notes
    ]

    return DashboardOut(
        counts=PipelineCounts(**counts),
        recent_transitions=recent_transitions,
        recent_notes=recent_notes,
    )
