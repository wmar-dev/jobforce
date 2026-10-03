from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing, StatusTransition
from jobforce.services.parse import normalize_description
from jobforce.services.storage import store_snapshot

logger = logging.getLogger(__name__)

# Valid pipeline state machine transitions
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "saved": ["applied", "rejected", "withdrawn", "archived", "shortlisted"],
    "archived": ["saved"],
    "shortlisted": ["applied", "rejected", "withdrawn", "archived", "saved"],
    "applied": ["interviewing", "rejected", "withdrawn"],
    "interviewing": ["offer", "rejected", "withdrawn"],
    "offer": [],
    "rejected": [],
    "withdrawn": [],
}

TERMINAL_STATUSES = {"offer", "rejected", "withdrawn"}


class IngestPayload(BaseModel):
    source_url: str
    html: str
    title: str
    company_name: str
    location: str | None = None
    role_type: str | None = None
    description: str | None = None
    posted_at: str | None = None


async def ingest_listing(
    session: AsyncSession,
    payload: IngestPayload,
    pages_dir: str = "backend/data/pages",
) -> dict[str, Any]:
    existing = await session.execute(
        select(JobListing).where(JobListing.source_url == payload.source_url)
    )
    existing_job = existing.scalar_one_or_none()
    if existing_job is not None:
        if payload.description:
            existing_job.description = normalize_description(payload.description)
        if payload.html:
            await store_snapshot(
                session, existing_job.id, payload.html.encode("utf-8"), pages_dir=pages_dir
            )
        await session.commit()
        return {
            "id": existing_job.id,
            "status": existing_job.status,
            "company_id": existing_job.company_id,
            "duplicate": True,
        }

    company = await _get_or_create_company(session, payload.company_name)
    now = datetime.now(UTC).isoformat()

    job = JobListing(
        company_id=company.id,
        title=payload.title,
        location=payload.location,
        role_type=payload.role_type,
        description=normalize_description(payload.description),
        posted_at=payload.posted_at,
        source_url=payload.source_url,
        status="saved",
        crawled_at=now,
    )
    session.add(job)
    await session.flush()

    transition = StatusTransition(
        job_listing_id=job.id,
        from_status=None,
        to_status="saved",
    )
    session.add(transition)

    html_bytes = payload.html.encode("utf-8")
    await store_snapshot(session, job.id, html_bytes, pages_dir=pages_dir)

    await session.commit()
    await session.refresh(job)

    logger.info("Ingested job listing id=%d title=%r company=%r", job.id, job.title, company.name)
    return {
        "id": job.id,
        "status": job.status,
        "company_id": company.id,
        "duplicate": False,
    }


async def bulk_archive_low_score(
    session: AsyncSession,
    company_id: int | None = None,
    all_active: bool = False,
    saved_only: bool = False,
) -> int:
    """Archive saved jobs with fit_score < 0.50. Optionally scoped to one company.

    With all_active=True (requires company_id), archives every saved/shortlisted
    job for that company regardless of fit score.

    With saved_only=True (requires company_id), archives every saved job for
    that company regardless of fit score, leaving shortlisted jobs untouched.
    """
    if all_active:
        conditions = [
            JobListing.status.in_(["saved", "shortlisted"]),
            JobListing.company_id == company_id,
        ]
    elif saved_only:
        conditions = [
            JobListing.status == "saved",
            JobListing.company_id == company_id,
        ]
    else:
        conditions = [
            JobListing.status == "saved",
            JobListing.fit_score.is_not(None),
            JobListing.fit_score < 0.50,
        ]
        if company_id is not None:
            conditions.append(JobListing.company_id == company_id)
    result = await session.execute(select(JobListing).where(*conditions))
    jobs = result.scalars().all()
    for job in jobs:
        old_status = job.status
        job.status = "archived"
        session.add(
            StatusTransition(
                job_listing_id=job.id,
                from_status=old_status,
                to_status="archived",
            )
        )
    await session.commit()
    logger.info("Bulk archived %d low-score jobs", len(jobs))
    return len(jobs)


async def transition_status(session: AsyncSession, job_id: int, new_status: str) -> dict[str, Any]:
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ValueError(f"Job listing {job_id} not found")

    allowed = _VALID_TRANSITIONS.get(job.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid transition: {job.status} → {new_status}",
        )

    old_status = job.status
    job.status = new_status
    transition = StatusTransition(
        job_listing_id=job_id,
        from_status=old_status,
        to_status=new_status,
    )
    session.add(transition)
    await session.commit()
    await session.refresh(transition)

    return {
        "id": job_id,
        "status": new_status,
        "transitioned_at": transition.transitioned_at,
    }


_LEGAL_SUFFIX = re.compile(
    r"[\s,]+(inc|incorporated|llc|ltd|corp|corporation|co)\.?$", re.IGNORECASE
)


def _company_key(name: str) -> str:
    """Case-insensitive company identity with trailing legal suffixes (Inc., LLC, ...) removed."""
    stripped = name.strip()
    return (_LEGAL_SUFFIX.sub("", stripped) or stripped).casefold()


async def _get_or_create_company(session: AsyncSession, name: str) -> Company:
    normalised = name.strip()
    key = _company_key(normalised)
    result = await session.execute(select(Company))
    company = next((c for c in result.scalars() if _company_key(c.name) == key), None)
    if company is None:
        company = Company(name=normalised)
        session.add(company)
        await session.flush()
    return company
