from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.config import AppConfig
from jobforce.db.models import Company, Resume, SearchConfigRecord

logger = logging.getLogger(__name__)

_RESUME_FILE = Path(__file__).parents[3] / "config" / "resume.json"


async def seed_from_config(session: AsyncSession, config: AppConfig) -> None:
    """Idempotent seed: insert new records, skip existing ones (by name / query+location)."""
    await _seed_companies(session, config)
    await _seed_search_configs(session, config)
    await _seed_base_resume(session)
    await session.commit()
    logger.info("Database seed complete.")


async def _seed_companies(session: AsyncSession, config: AppConfig) -> None:
    for company_cfg in config.search.target_companies:
        normalised = company_cfg.name.strip().lower()
        result = await session.execute(select(Company).where(Company.name.ilike(normalised)))
        if result.scalar_one_or_none() is None:
            session.add(Company(name=company_cfg.name.strip(), domain=company_cfg.domain or None))
            logger.info("Seeded company: %s", company_cfg.name)


async def _seed_base_resume(session: AsyncSession) -> None:
    if not _RESUME_FILE.exists():
        logger.warning("config/resume.json not found — skipping base resume seed.")
        return
    result = await session.execute(select(Resume).where(Resume.is_base == 1))
    if result.scalar_one_or_none() is not None:
        return
    structured_data = json.loads(_RESUME_FILE.read_text())
    session.add(Resume(label="Base Resume", is_base=1, structured_data=json.dumps(structured_data)))
    logger.info("Seeded base resume from config/resume.json.")


async def _seed_search_configs(session: AsyncSession, config: AppConfig) -> None:
    for query_cfg in config.search.queries:
        result = await session.execute(
            select(SearchConfigRecord).where(
                SearchConfigRecord.query == query_cfg.query,
                SearchConfigRecord.location == (query_cfg.location or None),
            )
        )
        if result.scalar_one_or_none() is None:
            session.add(
                SearchConfigRecord(
                    query=query_cfg.query,
                    location=query_cfg.location or None,
                    source=query_cfg.source or None,
                )
            )
            logger.info("Seeded search config: %s @ %s", query_cfg.query, query_cfg.location)


if __name__ == "__main__":
    import asyncio
    import logging
    import os

    logging.basicConfig(level=logging.INFO)
    from jobforce.config import load_config
    from jobforce.db.engine import get_session_factory, init_engine

    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.normpath(os.path.join(_here, "..", "..", ".."))
    config = load_config(os.path.join(_root, "config.yaml"))
    init_engine(config.database.path)

    async def _run() -> None:
        async with get_session_factory()() as session:
            await seed_from_config(session, config)

    asyncio.run(_run())
