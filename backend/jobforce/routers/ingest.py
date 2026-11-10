from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.routers.resume_schema import PipelineStatusStr
from jobforce.services.scout import IngestPayload, ingest_listing

router = APIRouter(tags=["scout"])


class IngestResponse(BaseModel):
    """The created listing, or the existing one when the URL was already captured."""

    id: int
    status: PipelineStatusStr
    company_id: int
    duplicate: bool


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=201,
    summary="Capture a job listing",
    responses={
        409: {
            "model": IngestResponse,
            "description": "Duplicate: source_url already captured; body is the existing job",
        }
    },
)
async def post_ingest(
    payload: IngestPayload,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IngestResponse:
    """Store a listing posted by the Chrome extension or a crawler skill, creating
    the company if needed. Deduplicates on `source_url`: a repeat returns 409 with
    the existing job instead of creating a new one."""
    result = await ingest_listing(session, payload)
    if result["duplicate"]:
        response.status_code = 409
    return IngestResponse(**result)
