"""CLI: merge a duplicate company record into a canonical one.

Usage:
    python -m jobforce.cli.merge_companies <source_id> <target_id>

Reassigns job listings and meeting notes from <source_id> to <target_id>,
then deletes the <source_id> company record. Use when scout ingestion
creates a duplicate Company row (e.g. "Edisonscientific" vs "Edison Scientific").
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys


async def _run(source_id: int, target_id: int) -> dict:  # type: ignore[type-arg]
    from jobforce.config import load_config
    from jobforce.db.engine import build_engine, build_session_factory
    from jobforce.services.companies import merge_companies

    cfg = load_config()
    engine = build_engine(cfg.database.path)
    factory = build_session_factory(engine)
    try:
        async with factory() as session:
            return await merge_companies(session, source_id, target_id)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge a duplicate company into a canonical one")
    parser.add_argument("source_id", type=int, help="ID of the duplicate company to remove")
    parser.add_argument("target_id", type=int, help="ID of the canonical company to keep")
    args = parser.parse_args()

    try:
        result = asyncio.run(_run(args.source_id, args.target_id))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
