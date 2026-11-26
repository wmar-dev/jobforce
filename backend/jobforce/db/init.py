from __future__ import annotations

from contextlib import suppress

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from jobforce.db.engine import get_engine
from jobforce.db.models import Base


async def create_all() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent migration: add updated_at to meeting_notes for existing DBs.
        # SQLite raises OperationalError if the column already exists; safe to ignore.
        with suppress(OperationalError):
            await conn.execute(
                text("ALTER TABLE meeting_notes ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
            )
            await conn.execute(
                text("UPDATE meeting_notes SET updated_at = created_at WHERE updated_at = ''")
            )
        # Idempotent migration: add posted_at to job_listings for existing DBs.
        with suppress(OperationalError):
            await conn.execute(text("ALTER TABLE job_listings ADD COLUMN posted_at TEXT"))


if __name__ == "__main__":
    import asyncio
    import logging
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    from jobforce.config import load_config
    from jobforce.db.engine import init_engine

    # Look for config.yaml in the project root (one level up from backend/)
    _root = Path(__file__).resolve().parents[3]
    config = load_config(str(_root / "config.yaml"))
    Path(config.database.path).parent.mkdir(parents=True, exist_ok=True)
    init_engine(config.database.path)
    asyncio.run(create_all())
    print("Database initialized.")
