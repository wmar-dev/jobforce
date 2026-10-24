"""Companies router — GET /api/companies, GET /api/companies/{id}, PATCH /api/companies/{id}, POST /api/companies/{id}/merge, POST/GET /api/companies/{id}/notes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from jobforce.db.engine import get_session
from jobforce.db.models import Company, JobListing, MeetingNote

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyListItem(BaseModel):
    id: int
    name: str
    domain: str | None
    careers_url: str | None


class CompanyPatch(BaseModel):
    careers_url: str | None = None
    domain: str | None = None


class CompanyMerge(BaseModel):
    source_id: int


class JobListingSummary(BaseModel):
    id: int
    title: str
    status: str
    role_type: str | None
    location: str | None
    created_at: str
    fit_score: float | None
    fit_scored: bool


class NoteOut(BaseModel):
    id: int
    company_id: int
    content: str
    created_at: str


class CompanyDetail(BaseModel):
    id: int
    name: str
    domain: str | None
    careers_url: str | None
    listings: list[JobListingSummary]
    notes: list[NoteOut]


class NoteCreate(BaseModel):
    content: str


@router.get("", response_model=list[CompanyListItem])
async def list_companies(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CompanyListItem]:
    result = await session.execute(select(Company).order_by(Company.name))
    companies = result.scalars().all()
    return [
        CompanyListItem(
            id=c.id,
            name=c.name,
            domain=c.domain,
            careers_url=c.careers_url,
        )
        for c in companies
    ]


@router.patch("/{company_id}", response_model=CompanyListItem)
async def patch_company(
    company_id: int,
    body: CompanyPatch,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CompanyListItem:
    company = await session.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    if body.careers_url is not None:
        company.careers_url = body.careers_url
    if body.domain is not None:
        company.domain = body.domain
    await session.commit()
    await session.refresh(company)
    return CompanyListItem(
        id=company.id,
        name=company.name,
        domain=company.domain,
        careers_url=company.careers_url,
    )


@router.post("/{company_id}/merge", response_model=CompanyListItem)
async def merge_company(
    company_id: int,
    body: CompanyMerge,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CompanyListItem:
    """Fold ``source_id`` into ``company_id``: move its listings and notes, then delete it."""
    if body.source_id == company_id:
        raise HTTPException(status_code=422, detail="Cannot merge a company into itself")
    target = await session.get(Company, company_id)
    source = await session.get(Company, body.source_id)
    if target is None or source is None:
        raise HTTPException(status_code=404, detail="Company not found")

    await session.execute(
        update(JobListing).where(JobListing.company_id == source.id).values(company_id=target.id)
    )
    await session.execute(
        update(MeetingNote).where(MeetingNote.company_id == source.id).values(company_id=target.id)
    )
    target.domain = target.domain or source.domain
    target.careers_url = target.careers_url or source.careers_url
    if source.notes:
        target.notes = f"{target.notes}\n{source.notes}" if target.notes else source.notes

    session.expire(source)
    await session.delete(source)
    await session.commit()
    await session.refresh(target)
    return CompanyListItem(
        id=target.id,
        name=target.name,
        domain=target.domain,
        careers_url=target.careers_url,
    )


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
            fit_score=j.fit_score,
            fit_scored=bool(j.fit_scored),
        )
        for j in sorted(
            company.job_listings,
            key=lambda j: (j.fit_score is None, -(j.fit_score or 0)),
        )
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
        careers_url=company.careers_url,
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
