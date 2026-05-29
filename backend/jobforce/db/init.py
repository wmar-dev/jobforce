from __future__ import annotations

from sqlalchemy import text

from jobforce.db.engine import get_engine
from jobforce.db.models import Base


async def create_all() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Idempotent migration: add updated_at to meeting_notes for existing DBs.
        # SQLite raises OperationalError if the column already exists; safe to ignore.
        try:
            await conn.execute(text(
                "ALTER TABLE meeting_notes ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''"
            ))
            await conn.execute(text(
                "UPDATE meeting_notes SET updated_at = created_at WHERE updated_at = ''"
            ))
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    import asyncio
    import logging
    import os
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    from jobforce.config import load_config
    from jobforce.db.engine import init_engine

    # Look for config.yaml in the project root (one level up from backend/)
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.normpath(os.path.join(_here, "..", "..", ".."))
    config = load_config(os.path.join(_root, "config.yaml"))
    Path(config.database.path).parent.mkdir(parents=True, exist_ok=True)
    init_engine(config.database.path)
    asyncio.run(create_all())
    print("Database initialized.")
