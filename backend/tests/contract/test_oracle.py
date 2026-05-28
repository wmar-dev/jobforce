"""Contract tests for Oracle ranking endpoints.

POST /api/oracle/rank — now returns 501 (ranking done by Claude Code skill).
GET /api/oracle/rank/{id} — returns stored fit score for a job.
PATCH /api/jobs/{id} — used by the oracle-rank skill to write scores.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _ingest(
    client: AsyncClient, url: str, title: str, description: str = "Python role"
) -> dict:
    payload = {
        "source_url": url,
        "html": "<html>job</html>",
        "title": title,
        "company_name": "TestCo",
        "description": description,
    }
    resp = await client.post("/api/ingest", json=payload)
    assert resp.status_code in (201, 409)
    return resp.json()


async def _write_score(
    client: AsyncClient,
    job_id: int,
    score: float = 0.80,
    confidence: str = "high",
    rationale: str = "Good match",
    warning: str | None = None,
) -> None:
    resp = await client.patch(
        f"/api/jobs/{job_id}",
        json={
            "fit_score": score,
            "fit_scored": 1,
            "fit_confidence": confidence,
            "fit_rationale": rationale,
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_oracle_rank_post_returns_501(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/oracle/rank", json={})
    assert resp.status_code == 501


@pytest.mark.asyncio
async def test_oracle_rank_post_501_mentions_claude_code(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/oracle/rank", json={})
    data = resp.json()
    assert "Claude Code" in data.get("detail", "")


@pytest.mark.asyncio
async def test_oracle_rank_get_returns_stored_score(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/o/1", "Backend Engineer")
    await _write_score(test_client, j["id"], score=0.85, confidence="high", rationale="Great fit")

    resp = await test_client.get(f"/api/oracle/rank/{j['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == j["id"]
    assert abs(data["score"] - 0.85) < 0.001
    assert data["confidence"] == "high"
    assert data["rationale"] == "Great fit"


@pytest.mark.asyncio
async def test_oracle_rank_get_returns_404_for_unscored_job(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/o/2", "Unscored Job")
    resp = await test_client.get(f"/api/oracle/rank/{j['id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_oracle_rank_missing_job_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/oracle/rank/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_job_fit_score_persists(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/o/3", "Score Write Job")

    resp = await test_client.patch(
        f"/api/jobs/{j['id']}",
        json={
            "fit_score": 0.85,
            "fit_scored": 1,
            "fit_confidence": "high",
            "fit_rationale": "Strong match for the role.",
        },
    )
    assert resp.status_code == 200

    get_resp = await test_client.get(f"/api/jobs/{j['id']}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["fit_scored"] is True
    assert abs(data["fit_score"] - 0.85) < 0.001
    assert data["fit_confidence"] == "high"
    assert data["fit_rationale"] == "Strong match for the role."


@pytest.mark.asyncio
async def test_patch_job_fit_score_score_bounds(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/o/4", "Bounds Job")
    await _write_score(test_client, j["id"], score=0.0, confidence="low", rationale="No fit")

    get_resp = await test_client.get(f"/api/jobs/{j['id']}")
    data = get_resp.json()
    assert 0.0 <= data["fit_score"] <= 1.0


@pytest.mark.asyncio
async def test_patch_job_fit_score_overwrites_previous(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/o/5", "Overwrite Job")
    await _write_score(test_client, j["id"], score=0.5, confidence="medium", rationale="Initial")
    await _write_score(test_client, j["id"], score=0.9, confidence="high", rationale="Updated")

    get_resp = await test_client.get(f"/api/jobs/{j['id']}")
    data = get_resp.json()
    assert abs(data["fit_score"] - 0.9) < 0.001
    assert data["fit_confidence"] == "high"
    assert data["fit_rationale"] == "Updated"
