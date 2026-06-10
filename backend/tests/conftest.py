from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.engine import build_engine, build_session_factory
from jobforce.db.models import Base, Company, JobListing, StatusTransition


@pytest_asyncio.fixture
async def db_engine(tmp_path: Any) -> AsyncGenerator[Any, None]:
    db_path = str(tmp_path / "test.db")
    engine = build_engine(db_path)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    factory = build_session_factory(db_engine)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(
    db_engine: Any, monkeypatch: Any, tmp_path: Any
) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to a test FastAPI app with an in-memory SQLite DB."""
    import jobforce.db.engine as engine_module
    import jobforce.routers.forge as forge_router_module
    import jobforce.services.forge as forge_service_module
    from jobforce.main import create_app

    monkeypatch.setattr(engine_module, "_engine", db_engine)
    monkeypatch.setattr(engine_module, "_session_factory", build_session_factory(db_engine))
    # Forge endpoints read/write these paths directly (not via the DB) — point
    # them at tmp_path so tests never touch the real config/resume.json or output/.
    monkeypatch.setattr(forge_router_module, "_RESUME_FILE", tmp_path / "resume.json")
    monkeypatch.setattr(forge_service_module, "_OUTPUT_DIR", tmp_path / "output")

    async def noop_lifespan(app: Any) -> AsyncGenerator[None, None]:
        yield

    app = create_app()
    # Override lifespan to skip startup DB init (already done in fixture)
    from contextlib import asynccontextmanager

    app.router.lifespan_context = asynccontextmanager(noop_lifespan)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def sample_company(db_session: AsyncSession) -> Company:
    company = Company(name="Acme Corp", domain="acme.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def sample_job(db_session: AsyncSession, sample_company: Company) -> JobListing:
    job = JobListing(
        company_id=sample_company.id,
        title="Senior Python Engineer",
        location="Remote, US",
        role_type="full-time",
        source_url="https://jobs.example.com/posting/123",
        status="saved",
    )
    db_session.add(job)
    await db_session.flush()
    transition = StatusTransition(
        job_listing_id=job.id,
        from_status=None,
        to_status="saved",
    )
    db_session.add(transition)
    await db_session.commit()
    await db_session.refresh(job)
    return job
