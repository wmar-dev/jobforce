from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import get_session
from jobforce.services.scout import IngestPayload, ingest_listing

router = APIRouter(tags=["scout"])


class IngestResponse(BaseModel):
    id: int
    status: str
    company_id: int
    duplicate: bool


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def post_ingest(
    payload: IngestPayload,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IngestResponse:
    result = await ingest_listing(session, payload)
    if result["duplicate"]:
        response.status_code = 409
    return IngestResponse(**result)
