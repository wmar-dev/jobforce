"""Contract tests for Oracle ranking endpoints — POST /api/oracle/rank, GET /api/oracle/rank/{id}."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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


def _mock_rank_response(job_ids: list[int]) -> list[dict]:
    return [
        {
            "job_id": jid,
            "score": 0.85 - (i * 0.1),
            "confidence": "high" if i == 0 else "medium",
            "rationale": f"Good fit reason {i}",
            "warning": None,
        }
        for i, jid in enumerate(job_ids)
    ]


@pytest.mark.asyncio
async def test_oracle_rank_returns_ranked_array(test_client: AsyncClient) -> None:
    j1 = await _ingest(test_client, "https://example.com/o/1", "Backend Engineer")
    j2 = await _ingest(test_client, "https://example.com/o/2", "Frontend Engineer")

    mock_results = _mock_rank_response([j1["id"], j2["id"]])

    with patch(
        "jobforce.routers.oracle.rank_jobs",
        new_callable=AsyncMock,
        return_value=mock_results,
    ):
        resp = await test_client.post("/api/oracle/rank", json={"job_ids": [j1["id"], j2["id"]]})

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    first = data[0]
    assert "job_id" in first
    assert "score" in first
    assert "confidence" in first
    assert "rationale" in first
    assert 0.0 <= first["score"] <= 1.0
    assert first["confidence"] in ("high", "medium", "low")


@pytest.mark.asyncio
async def test_oracle_rank_results_ordered_by_score_descending(test_client: AsyncClient) -> None:
    j1 = await _ingest(test_client, "https://example.com/o/3", "Job High Score")
    j2 = await _ingest(test_client, "https://example.com/o/4", "Job Low Score")

    mock_results = [
        {
            "job_id": j1["id"],
            "score": 0.9,
            "confidence": "high",
            "rationale": "Great",
            "warning": None,
        },
        {
            "job_id": j2["id"],
            "score": 0.4,
            "confidence": "low",
            "rationale": "Poor",
            "warning": None,
        },
    ]

    with patch(
        "jobforce.routers.oracle.rank_jobs",
        new_callable=AsyncMock,
        return_value=mock_results,
    ):
        resp = await test_client.post("/api/oracle/rank", json={})

    assert resp.status_code == 200
    data = resp.json()
    scores = [r["score"] for r in data]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_oracle_rank_sparse_description_returns_low_confidence_and_warning(
    test_client: AsyncClient,
) -> None:
    j = await _ingest(test_client, "https://example.com/o/5", "Sparse Job", description="short")

    mock_results = [
        {
            "job_id": j["id"],
            "score": 0.3,
            "confidence": "low",
            "rationale": "Insufficient description",
            "warning": "Job description is too sparse for reliable scoring",
        }
    ]

    with patch(
        "jobforce.routers.oracle.rank_jobs",
        new_callable=AsyncMock,
        return_value=mock_results,
    ):
        resp = await test_client.post("/api/oracle/rank", json={"job_ids": [j["id"]]})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    result = data[0]
    assert result["confidence"] == "low"
    assert result["warning"] is not None
    assert len(result["warning"]) > 0


@pytest.mark.asyncio
async def test_oracle_rank_result_stored_and_retrievable_by_job_id(
    test_client: AsyncClient,
) -> None:
    j = await _ingest(test_client, "https://example.com/o/6", "Cached Job")

    mock_results = [
        {
            "job_id": j["id"],
            "score": 0.75,
            "confidence": "medium",
            "rationale": "Decent fit",
            "warning": None,
        }
    ]

    with patch(
        "jobforce.routers.oracle.rank_jobs",
        new_callable=AsyncMock,
        return_value=mock_results,
    ):
        await test_client.post("/api/oracle/rank", json={"job_ids": [j["id"]]})

    resp = await test_client.get(f"/api/oracle/rank/{j['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == j["id"]
    assert "score" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_oracle_rank_missing_job_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/oracle/rank/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_oracle_rank_updates_job_listing_fit_fields(test_client: AsyncClient) -> None:
    j = await _ingest(test_client, "https://example.com/o/7", "Scored Job")

    mock_results = [
        {
            "job_id": j["id"],
            "score": 0.88,
            "confidence": "high",
            "rationale": "Excellent",
            "warning": None,
        }
    ]

    with patch(
        "jobforce.routers.oracle.rank_jobs",
        new_callable=AsyncMock,
        return_value=mock_results,
    ):
        await test_client.post("/api/oracle/rank", json={"job_ids": [j["id"]]})

    resp = await test_client.get(f"/api/jobs/{j['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["fit_scored"] is True
    assert data["fit_score"] is not None
    assert 0.0 <= data["fit_score"] <= 1.0
    assert data["fit_confidence"] in ("high", "medium", "low")
