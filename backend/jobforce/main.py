from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from jobforce.config import get_config
from jobforce.db.engine import get_session_factory, init_engine
from jobforce.db.init import create_all
from jobforce.db.seed import seed_from_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    config = get_config()
    init_engine(config.database.path)
    await create_all()
    async with get_session_factory()() as session:
        await seed_from_config(session, config)
        from jobforce.services.storage import verify_integrity

        missing = await verify_integrity(session)
        if missing:
            logger.warning(
                "Storage integrity check: %d missing file(s): %s",
                len(missing),
                missing[:5],
            )
        else:
            logger.info("Storage integrity check passed.")
    logger.info("Jobforce backend started.")
    yield
    logger.info("Jobforce backend shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(title="Jobforce API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: object) -> Response:
        start = time.monotonic()
        response: Response = await call_next(request)  # type: ignore[operator]
        duration_ms = (time.monotonic() - start) * 1000
        path = request.url.path
        if any(path.startswith(p) for p in ("/api/oracle", "/api/forge", "/api/coach")):
            logger.info(
                "AI_CALL path=%s method=%s status=%d duration_ms=%.1f",
                path,
                request.method,
                response.status_code,
                duration_ms,
            )
        else:
            logger.info(
                "REQUEST path=%s method=%s status=%d duration_ms=%.1f",
                path,
                request.method,
                response.status_code,
                duration_ms,
            )
        return response

    # Routers registered here — imported lazily to avoid circular imports
    from jobforce.routers import coach, companies, dashboard, forge, ingest, jobs, oracle

    app.include_router(ingest.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(oracle.router, prefix="/api")
    app.include_router(forge.router, prefix="/api")
    app.include_router(coach.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(companies.router, prefix="/api")

    return app


app = create_app()
