"""Unit tests for triage status transitions (archived, shortlisted) and default exclusion."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company, JobListing
from jobforce.services.scout import _VALID_TRANSITIONS

# ---------------------------------------------------------------------------
# Transition graph tests (T012 / T020)
# ---------------------------------------------------------------------------


def test_saved_can_transition_to_archived() -> None:
    assert "archived" in _VALID_TRANSITIONS["saved"]


def test_saved_can_transition_to_shortlisted() -> None:
    assert "shortlisted" in _VALID_TRANSITIONS["saved"]


def test_archived_can_restore_to_saved() -> None:
    assert "saved" in _VALID_TRANSITIONS["archived"]


def test_shortlisted_can_transition_to_saved() -> None:
    assert "saved" in _VALID_TRANSITIONS["shortlisted"]


def test_shortlisted_can_transition_to_applied() -> None:
    assert "applied" in _VALID_TRANSITIONS["shortlisted"]


def test_shortlisted_can_transition_to_archived() -> None:
    assert "archived" in _VALID_TRANSITIONS["shortlisted"]


def test_archived_cannot_transition_to_shortlisted() -> None:
    # archived → shortlisted is not in the graph; restore to saved first
    assert "shortlisted" not in _VALID_TRANSITIONS["archived"]


def test_terminal_statuses_have_no_transitions() -> None:
    for status in ("offer", "rejected", "withdrawn"):
        assert _VALID_TRANSITIONS[status] == []


# ---------------------------------------------------------------------------
# Default GET /api/jobs exclusion tests (T007 / T009) — via HTTP client
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_default_list_excludes_archived(
    test_client: object, db_session: AsyncSession, sample_company: Company
) -> None:
    archived_job = JobListing(
        company_id=sample_company.id,
        title="Archived Job",
        source_url="https://example.com/archived",
        status="archived",
    )
    saved_job = JobListing(
        company_id=sample_company.id,
        title="Saved Job",
        source_url="https://example.com/saved",
        status="saved",
    )
    db_session.add_all([archived_job, saved_job])
    await db_session.commit()

    from httpx import AsyncClient

    assert isinstance(test_client, AsyncClient)
    response = await test_client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    statuses = {j["status"] for j in data["items"]}
    assert "archived" not in statuses
    assert "saved" in statuses


@pytest.mark.asyncio
async def test_default_list_excludes_withdrawn(
    test_client: object, db_session: AsyncSession, sample_company: Company
) -> None:
    withdrawn_job = JobListing(
        company_id=sample_company.id,
        title="Withdrawn Job",
        source_url="https://example.com/withdrawn",
        status="withdrawn",
    )
    saved_job = JobListing(
        company_id=sample_company.id,
        title="Saved Job 2",
        source_url="https://example.com/saved2-active",
        status="saved",
    )
    db_session.add_all([withdrawn_job, saved_job])
    await db_session.commit()

    from httpx import AsyncClient

    assert isinstance(test_client, AsyncClient)
    response = await test_client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    statuses = {j["status"] for j in data["items"]}
    assert "withdrawn" not in statuses
    assert "saved" in statuses


@pytest.mark.asyncio
async def test_explicit_withdrawn_filter_returns_only_withdrawn(
    test_client: object, db_session: AsyncSession, sample_company: Company
) -> None:
    withdrawn_job = JobListing(
        company_id=sample_company.id,
        title="Withdrawn Job 2",
        source_url="https://example.com/withdrawn2",
        status="withdrawn",
    )
    saved_job = JobListing(
        company_id=sample_company.id,
        title="Saved Job 3",
        source_url="https://example.com/saved3-active",
        status="saved",
    )
    db_session.add_all([withdrawn_job, saved_job])
    await db_session.commit()

    from httpx import AsyncClient

    assert isinstance(test_client, AsyncClient)
    response = await test_client.get("/api/jobs?status=withdrawn")
    assert response.status_code == 200
    data = response.json()
    statuses = {j["status"] for j in data["items"]}
    assert statuses == {"withdrawn"}


@pytest.mark.asyncio
async def test_default_list_excludes_rejected(
    test_client: object, db_session: AsyncSession, sample_company: Company
) -> None:
    rejected_job = JobListing(
        company_id=sample_company.id,
        title="Rejected Job",
        source_url="https://example.com/rejected",
        status="rejected",
    )
    saved_job = JobListing(
        company_id=sample_company.id,
        title="Saved Job 4",
        source_url="https://example.com/saved4-active",
        status="saved",
    )
    db_session.add_all([rejected_job, saved_job])
    await db_session.commit()

    from httpx import AsyncClient

    assert isinstance(test_client, AsyncClient)
    response = await test_client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    statuses = {j["status"] for j in data["items"]}
    assert "rejected" not in statuses
    assert "saved" in statuses


@pytest.mark.asyncio
async def test_explicit_rejected_filter_returns_only_rejected(
    test_client: object, db_session: AsyncSession, sample_company: Company
) -> None:
    rejected_job = JobListing(
        company_id=sample_company.id,
        title="Rejected Job 2",
        source_url="https://example.com/rejected2",
        status="rejected",
    )
    saved_job = JobListing(
        company_id=sample_company.id,
        title="Saved Job 5",
        source_url="https://example.com/saved5-active",
        status="saved",
    )
    db_session.add_all([rejected_job, saved_job])
    await db_session.commit()

    from httpx import AsyncClient

    assert isinstance(test_client, AsyncClient)
    response = await test_client.get("/api/jobs?status=rejected")
    assert response.status_code == 200
    data = response.json()
    statuses = {j["status"] for j in data["items"]}
    assert statuses == {"rejected"}


@pytest.mark.asyncio
async def test_explicit_archived_filter_returns_only_archived(
    test_client: object, db_session: AsyncSession, sample_company: Company
) -> None:
    archived_job = JobListing(
        company_id=sample_company.id,
        title="Archived Job",
        source_url="https://example.com/archived2",
        status="archived",
    )
    saved_job = JobListing(
        company_id=sample_company.id,
        title="Saved Job",
        source_url="https://example.com/saved2",
        status="saved",
    )
    db_session.add_all([archived_job, saved_job])
    await db_session.commit()

    from httpx import AsyncClient

    assert isinstance(test_client, AsyncClient)
    response = await test_client.get("/api/jobs?status=archived")
    assert response.status_code == 200
    data = response.json()
    statuses = {j["status"] for j in data["items"]}
    assert statuses == {"archived"}
