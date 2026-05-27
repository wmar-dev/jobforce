from __future__ import annotations

from jobforce.db.engine import get_engine
from jobforce.db.models import Base


async def create_all() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
