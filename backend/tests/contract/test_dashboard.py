"""Contract tests for HQ Dashboard and Companies endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _ingest(client: AsyncClient, url: str, title: str, company: str = "DashCo") -> dict:
    payload = {
        "source_url": url,
        "html": "<html>job</html>",
        "title": title,
        "company_name": company,
    }
    resp = await client.post("/api/ingest", json=payload)
    assert resp.status_code in (201, 409)
    return resp.json()


async def _transition(client: AsyncClient, job_id: int, status: str) -> None:
    resp = await client.patch(f"/api/jobs/{job_id}/status", json={"status": status})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_returns_pipeline_counts(test_client: AsyncClient) -> None:
    j1 = await _ingest(test_client, "https://example.com/d/1", "Job 1")
    j2 = await _ingest(test_client, "https://example.com/d/2", "Job 2")
    await _transition(test_client, j1["id"], "applied")
    await _transition(test_client, j2["id"], "applied")
    await _transition(test_client, j2["id"], "interviewing")

    resp = await test_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    assert "counts" in data
    counts = data["counts"]
    for status in ("saved", "applied", "interviewing", "offer", "rejected", "withdrawn"):
        assert status in counts
        assert isinstance(counts[status], int)

    assert counts["applied"] >= 1
    assert counts["interviewing"] >= 1


@pytest.mark.asyncio
async def test_dashboard_counts_include_withdrawn(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/d/3", "Withdrawn Job")
    await _transition(test_client, j["id"], "withdrawn")

    resp = await test_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["counts"]["withdrawn"] >= 1


@pytest.mark.asyncio
async def test_dashboard_includes_recent_transitions(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/d/4", "Activity Job")
    await _transition(test_client, j["id"], "applied")

    resp = await test_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "recent_transitions" in data
    assert isinstance(data["recent_transitions"], list)
    assert len(data["recent_transitions"]) >= 1
    transition = data["recent_transitions"][0]
    assert "to_status" in transition
    assert "job_title" in transition or "job_id" in transition


@pytest.mark.asyncio
async def test_dashboard_includes_recent_notes(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/d/5", "Notes Job", company="NotesCo")
    company_id = j["company_id"]

    await test_client.post(
        f"/api/companies/{company_id}/notes",
        json={"content": "Great culture, team of 10"},
    )

    resp = await test_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "recent_notes" in data
    assert isinstance(data["recent_notes"], list)


@pytest.mark.asyncio
async def test_post_company_note_creates_note(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/d/6", "Note Target", company="NoteTarget")
    company_id = j["company_id"]

    resp = await test_client.post(
        f"/api/companies/{company_id}/notes",
        json={"content": "Met with the hiring manager"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Met with the hiring manager"
    assert data["company_id"] == company_id
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_company_notes_returns_reverse_chronological(test_client: AsyncClient) -> None:
    j = await _ingest(
        test_client, "https://example.com/d/7", "Multi Note Job", company="MultiNoteCo"
    )
    company_id = j["company_id"]

    await test_client.post(f"/api/companies/{company_id}/notes", json={"content": "First note"})
    await test_client.post(f"/api/companies/{company_id}/notes", json={"content": "Second note"})
    await test_client.post(f"/api/companies/{company_id}/notes", json={"content": "Third note"})

    resp = await test_client.get(f"/api/companies/{company_id}/notes")
    assert resp.status_code == 200
    notes = resp.json()
    assert isinstance(notes, list)
    assert len(notes) >= 3
    # Most recent first
    assert notes[0]["content"] == "Third note"
    assert notes[1]["content"] == "Second note"


@pytest.mark.asyncio
async def test_get_company_detail_includes_listings_and_notes(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/d/8", "Embedded Job", company="EmbedCo")
    company_id = j["company_id"]
    await test_client.post(f"/api/companies/{company_id}/notes", json={"content": "Key insight"})

    resp = await test_client.get(f"/api/companies/{company_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "name" in data
    assert "listings" in data
    assert isinstance(data["listings"], list)
    assert len(data["listings"]) >= 1
    assert "notes" in data
    assert isinstance(data["notes"], list)
    assert len(data["notes"]) >= 1


@pytest.mark.asyncio
async def test_get_company_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/companies/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_post_note_to_nonexistent_company_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/companies/99999/notes",
        json={"content": "Ghost note"},
    )
    assert resp.status_code == 404


async def _company_id(client: AsyncClient, name: str) -> int:
    companies = (await client.get("/api/companies")).json()
    return next(c["id"] for c in companies if c["name"] == name)


@pytest.mark.asyncio
async def test_merge_company_moves_listings_and_notes(test_client: AsyncClient) -> None:
    keep = await _ingest(test_client, "https://example.com/m/1", "Keep Job", "MergeCo")
    drop = await _ingest(test_client, "https://example.com/m/2", "Drop Job", "Merge Co Labs")
    keep_id = await _company_id(test_client, "MergeCo")
    drop_id = await _company_id(test_client, "Merge Co Labs")
    assert keep_id != drop_id
    await test_client.post(f"/api/companies/{drop_id}/notes", json={"content": "Recruiter call"})

    resp = await test_client.post(f"/api/companies/{keep_id}/merge", json={"source_id": drop_id})
    assert resp.status_code == 200
    assert resp.json()["id"] == keep_id

    detail = (await test_client.get(f"/api/companies/{keep_id}")).json()
    assert {j["id"] for j in detail["listings"]} == {keep["id"], drop["id"]}
    assert len(detail["notes"]) == 1
    assert (await test_client.get(f"/api/companies/{drop_id}")).status_code == 404


@pytest.mark.asyncio
async def test_merge_company_into_itself_returns_422(test_client: AsyncClient) -> None:
    await _ingest(test_client, "https://example.com/m/3", "Self Job", "SelfCo")
    cid = await _company_id(test_client, "SelfCo")
    resp = await test_client.post(f"/api/companies/{cid}/merge", json={"source_id": cid})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_merge_company_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/companies/99998/merge", json={"source_id": 99999})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ingest_matches_company_ignoring_legal_suffix(test_client: AsyncClient) -> None:
    await _ingest(test_client, "https://example.com/s/1", "Job A", "SuffixCo")
    await _ingest(test_client, "https://example.com/s/2", "Job B", "suffixco, Inc.")
    companies = (await test_client.get("/api/companies")).json()
    assert len([c for c in companies if c["name"].lower().startswith("suffixco")]) == 1
