"""Integration tests for companies endpoints — GET /api/companies, PATCH /api/companies/{id}."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import Company


@pytest.mark.asyncio
async def test_list_companies_returns_seeded(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    company = Company(name="Test Co", domain="testco.com", careers_url="https://testco.com/jobs")
    db_session.add(company)
    await db_session.commit()

    response = await test_client.get("/api/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [c["name"] for c in data]
    assert "Test Co" in names
    match = next(c for c in data if c["name"] == "Test Co")
    assert match["domain"] == "testco.com"
    assert match["careers_url"] == "https://testco.com/jobs"


@pytest.mark.asyncio
async def test_list_companies_empty(test_client: AsyncClient) -> None:
    response = await test_client.get("/api/companies")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_patch_company_updates_careers_url(
    test_client: AsyncClient, db_session: AsyncSession
) -> None:
    company = Company(name="Patch Co", domain="patchco.com")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    response = await test_client.patch(
        f"/api/companies/{company.id}",
        json={"careers_url": "https://boards.greenhouse.io/patchco"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["careers_url"] == "https://boards.greenhouse.io/patchco"
    assert data["id"] == company.id

    # Verify persisted
    await db_session.refresh(company)
    assert company.careers_url == "https://boards.greenhouse.io/patchco"


@pytest.mark.asyncio
async def test_patch_company_not_found(test_client: AsyncClient) -> None:
    response = await test_client.patch(
        "/api/companies/99999",
        json={"careers_url": "https://example.com/jobs"},
    )
    assert response.status_code == 404
