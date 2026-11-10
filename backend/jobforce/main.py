from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from jobforce.config import get_config
from jobforce.db.engine import get_session_factory, init_engine
from jobforce.db.init import create_all
from jobforce.db.seed import seed_from_config
from jobforce.routers.errors import ApiError, api_error_handler
from jobforce.routers.resume_schema import add_resume_components

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Order matches router registration below; descriptions render as group headers in /docs.
OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "scout", "description": "Capture job listings from the extension and crawlers."},
    {"name": "jobs", "description": "Browse, edit, and move job listings through the pipeline."},
    {"name": "oracle", "description": "Read fit scores written by the /oracle-rank skill."},
    {"name": "forge", "description": "Base and tailored resumes, diff, and PDF export."},
    {"name": "coach", "description": "Interview prep sessions written by the /coach-prep skill."},
    {"name": "dashboard", "description": "Pipeline summary counts and recent activity."},
    {"name": "companies", "description": "Target companies, merge, and recruiter notes."},
]


def _api_version() -> str:
    try:
        return version("jobforce")
    except PackageNotFoundError:
        return "0.1.0"


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


def _register_extra_schemas(app: FastAPI) -> None:
    """Add components FastAPI can't discover because their fields are typed Any."""
    generate = app.openapi

    def openapi() -> dict[str, Any]:
        return add_resume_components(generate())

    app.openapi = openapi  # type: ignore[method-assign]


def create_app() -> FastAPI:
    app = FastAPI(
        title="Jobforce API",
        version=_api_version(),
        description=(
            "Local API behind the Jobforce dashboard, Chrome extension, and Claude Code "
            "skills. Business errors return `{detail, code}`; branch on `code`."
        ),
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    app.add_exception_handler(ApiError, api_error_handler)
    _register_extra_schemas(app)

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
