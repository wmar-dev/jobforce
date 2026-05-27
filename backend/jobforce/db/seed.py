from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.config import AppConfig
from jobforce.db.models import Company, SearchConfigRecord

logger = logging.getLogger(__name__)


async def seed_from_config(session: AsyncSession, config: AppConfig) -> None:
    """Idempotent seed: insert new records, skip existing ones (by name / query+location)."""
    await _seed_companies(session, config)
    await _seed_search_configs(session, config)
    await session.commit()
    logger.info("Database seed complete.")


async def _seed_companies(session: AsyncSession, config: AppConfig) -> None:
    for company_cfg in config.search.target_companies:
        normalised = company_cfg.name.strip().lower()
        result = await session.execute(
            select(Company).where(Company.name.ilike(normalised))
        )
        if result.scalar_one_or_none() is None:
            session.add(Company(name=company_cfg.name.strip(), domain=company_cfg.domain or None))
            logger.info("Seeded company: %s", company_cfg.name)


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
