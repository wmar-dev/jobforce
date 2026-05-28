"""Companies router — GET /api/companies/{id}, POST/GET /api/companies/{id}/notes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jobforce.db.engine import get_session
from jobforce.db.models import Company, MeetingNote

router = APIRouter(prefix="/companies", tags=["companies"])


class JobListingSummary(BaseModel):
    id: int
    title: str
    status: str
    role_type: str | None
    location: str | None
    created_at: str


class NoteOut(BaseModel):
    id: int
    company_id: int
    content: str
    created_at: str


class CompanyDetail(BaseModel):
    id: int
    name: str
    domain: str | None
    listings: list[JobListingSummary]
    notes: list[NoteOut]


class NoteCreate(BaseModel):
    content: str


@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(
    company_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CompanyDetail:
    result = await session.execute(
        select(Company)
        .options(
            selectinload(Company.job_listings),
            selectinload(Company.meeting_notes),
        )
        .where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    listings = [
        JobListingSummary(
            id=j.id,
            title=j.title,
            status=j.status,
            role_type=j.role_type,
            location=j.location,
            created_at=j.created_at,
        )
        for j in company.job_listings
    ]

    notes = [
        NoteOut(
            id=n.id,
            company_id=n.company_id,
            content=n.body,
            created_at=n.created_at,
        )
        for n in sorted(company.meeting_notes, key=lambda n: n.created_at, reverse=True)
    ]

    return CompanyDetail(
        id=company.id,
        name=company.name,
        domain=company.domain,
        listings=listings,
        notes=notes,
    )


@router.post("/{company_id}/notes", response_model=NoteOut, status_code=201)
async def create_note(
    company_id: int,
    body: NoteCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> NoteOut:
    company = await session.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    note = MeetingNote(
        company_id=company_id,
        body=body.content,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    return NoteOut(
        id=note.id,
        company_id=note.company_id,
        content=note.body,
        created_at=note.created_at,
    )


@router.get("/{company_id}/notes", response_model=list[NoteOut])
async def get_notes(
    company_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[NoteOut]:
    company = await session.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    result = await session.execute(
        select(MeetingNote)
        .where(MeetingNote.company_id == company_id)
        .order_by(MeetingNote.created_at.desc())
    )
    notes = result.scalars().all()

    return [
        NoteOut(
            id=n.id,
            company_id=n.company_id,
            content=n.body,
            created_at=n.created_at,
        )
        for n in notes
    ]
