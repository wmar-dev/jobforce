"""Profile router — GET /api/profile, PUT /api/profile."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.db.models import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileOut(BaseModel):
    id: int
    full_name: str | None
    headline: str | None
    skills: str | None
    experience: str | None
    preferences: str | None
    updated_at: str


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    headline: str | None = None
    skills: str | None = None
    experience: str | None = None
    preferences: str | None = None


@router.get("", response_model=ProfileOut)
async def get_profile(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProfileOut:
    profile = await session.get(UserProfile, 1)
    if profile is None:
        from jobforce.db.models import _now

        profile = UserProfile(id=1, updated_at=_now())
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return ProfileOut(
        id=profile.id,
        full_name=profile.full_name,
        headline=profile.headline,
        skills=profile.skills,
        experience=profile.experience,
        preferences=profile.preferences,
        updated_at=profile.updated_at,
    )


@router.put("", response_model=ProfileOut)
async def put_profile(
    body: ProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProfileOut:
    profile = await session.get(UserProfile, 1)
    if profile is None:
        from jobforce.db.models import _now

        profile = UserProfile(id=1, updated_at=_now())
        session.add(profile)
        await session.flush()

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await session.commit()
    await session.refresh(profile)
    return ProfileOut(
        id=profile.id,
        full_name=profile.full_name,
        headline=profile.headline,
        skills=profile.skills,
        experience=profile.experience,
        preferences=profile.preferences,
        updated_at=profile.updated_at,
    )
