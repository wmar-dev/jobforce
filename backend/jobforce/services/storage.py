from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import PageSnapshot

logger = logging.getLogger(__name__)

BLOB_THRESHOLD_BYTES = 500 * 1024  # 500 KB


async def store_snapshot(
    session: AsyncSession,
    job_listing_id: int,
    html_bytes: bytes,
    pages_dir: str = "backend/data/pages",
) -> PageSnapshot:
    content_hash = hashlib.sha256(html_bytes).hexdigest()
    size = len(html_bytes)

    if size <= BLOB_THRESHOLD_BYTES:
        snapshot = PageSnapshot(
            job_listing_id=job_listing_id,
            html_blob=html_bytes,
            file_path=None,
            content_hash=content_hash,
            size_bytes=size,
        )
    else:
        Path(pages_dir).mkdir(parents=True, exist_ok=True)
        file_path = str(Path(pages_dir) / f"{job_listing_id}_{content_hash[:16]}.html")
        Path(file_path).write_bytes(html_bytes)
        snapshot = PageSnapshot(
            job_listing_id=job_listing_id,
            html_blob=None,
            file_path=file_path,
            content_hash=content_hash,
            size_bytes=size,
        )

    # Delete any stale snapshot for this job_listing_id (can exist if SQLite
    # recycled an id after a row was deleted from job_listings).
    existing = await session.execute(
        select(PageSnapshot).where(PageSnapshot.job_listing_id == job_listing_id)
    )
    stale = existing.scalar_one_or_none()
    if stale is not None:
        await session.delete(stale)
        await session.flush()

    session.add(snapshot)
    await session.flush()
    return snapshot


async def retrieve_snapshot(session: AsyncSession, job_listing_id: int) -> bytes | None:
    result = await session.execute(
        select(PageSnapshot).where(PageSnapshot.job_listing_id == job_listing_id)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        return None
    if snapshot.html_blob is not None:
        return snapshot.html_blob
    if snapshot.file_path and Path(snapshot.file_path).exists():
        return Path(snapshot.file_path).read_bytes()
    return None


async def verify_integrity(session: AsyncSession) -> list[str]:
    result = await session.execute(select(PageSnapshot).where(PageSnapshot.file_path.is_not(None)))
    snapshots = result.scalars().all()
    missing = []
    for snap in snapshots:
        if snap.file_path and not Path(snap.file_path).exists():
            logger.warning(
                "Missing snapshot file: %s (job_listing_id=%d)", snap.file_path, snap.job_listing_id
            )
            missing.append(snap.file_path)
    return missing
