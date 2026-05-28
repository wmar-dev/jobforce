"""Contract tests for Coach interview preparation endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _ingest_job(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/ingest",
        json={
            "source_url": "https://example.com/coach/job1",
            "html": "<html>job</html>",
            "title": "Senior Software Engineer",
            "company_name": "TechCo",
            "description": "Python, system design, algorithms, distributed systems",
        },
    )
    assert resp.status_code in (201, 409)
    return resp.json()


def _mock_prep_session(job_id: int) -> dict:
    return {
        "session_id": 1,
        "job_id": job_id,
        "questions": [
            {
                "id": "q1",
                "category": "behavioral",
                "text": "Tell me about a time you led a team under pressure.",
                "source_url": "https://glassdoor.com/interview/techco",
                "leetcode_url": None,
                "guidance": "Use the STAR method",
            },
            {
                "id": "q2",
                "category": "coding",
                "text": "Implement a LRU cache.",
                "source_url": None,
                "leetcode_url": "https://leetcode.com/problems/lru-cache/",
                "guidance": "Use OrderedDict or a doubly-linked list",
            },
            {
                "id": "q3",
                "category": "system_design",
                "text": "Design a URL shortener.",
                "source_url": None,
                "leetcode_url": None,
                "guidance": "Consider hashing strategies and database choices",
            },
            {
                "id": "q4",
                "category": "role_specific",
                "text": "How would you optimize a slow SQLAlchemy query?",
                "source_url": None,
                "leetcode_url": None,
                "guidance": "Think about N+1 queries and eager loading",
            },
        ],
    }


@pytest.mark.asyncio
async def test_coach_prep_returns_session_with_all_four_categories(
    test_client: AsyncClient,
) -> None:
    job = await _ingest_job(test_client)
    mock_session = _mock_prep_session(job["id"])

    with patch(
        "jobforce.routers.coach.generate_prep_pack",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        resp = await test_client.post("/api/coach/prep", json={"job_id": job["id"]})

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "questions" in data
    questions = data["questions"]
    assert len(questions) >= 4
    categories = {q["category"] for q in questions}
    for expected_cat in ("behavioral", "coding", "system_design", "role_specific"):
        assert expected_cat in categories, f"Missing category: {expected_cat}"


@pytest.mark.asyncio
async def test_coach_prep_coding_question_has_leetcode_url(
    test_client: AsyncClient,
) -> None:
    job = await _ingest_job(test_client)
    mock_session = _mock_prep_session(job["id"])

    with patch(
        "jobforce.routers.coach.generate_prep_pack",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        resp = await test_client.post("/api/coach/prep", json={"job_id": job["id"]})

    assert resp.status_code == 200
    data = resp.json()
    coding_questions = [q for q in data["questions"] if q["category"] == "coding"]
    assert len(coding_questions) >= 1
    assert any(q.get("leetcode_url") for q in coding_questions)


@pytest.mark.asyncio
async def test_coach_prep_job_not_found_returns_404(test_client: AsyncClient) -> None:
    resp = await test_client.post("/api/coach/prep", json={"job_id": 99999})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_submit_answer_returns_feedback_and_score(test_client: AsyncClient) -> None:
    job = await _ingest_job(test_client)
    mock_session = _mock_prep_session(job["id"])

    with patch(
        "jobforce.routers.coach.generate_prep_pack",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        prep_resp = await test_client.post("/api/coach/prep", json={"job_id": job["id"]})

    session_id = prep_resp.json()["session_id"]

    mock_feedback = {
        "question_id": "q1",
        "feedback": "Good use of STAR method. Add more context about the outcome.",
        "score": 0.75,
    }

    with patch(
        "jobforce.routers.coach.evaluate_answer",
        new_callable=AsyncMock,
        return_value=mock_feedback,
    ):
        resp = await test_client.post(
            f"/api/coach/sessions/{session_id}/answer",
            json={
                "question_id": "q1",
                "answer": "I led a team of 5 engineers during a production incident.",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "feedback" in data
    assert "score" in data
    assert 0.0 <= data["score"] <= 1.0
    assert len(data["feedback"]) > 0


@pytest.mark.asyncio
async def test_session_summary_returns_overall_score_and_areas(
    test_client: AsyncClient,
) -> None:
    job = await _ingest_job(test_client)
    mock_session = _mock_prep_session(job["id"])

    with patch(
        "jobforce.routers.coach.generate_prep_pack",
        new_callable=AsyncMock,
        return_value=mock_session,
    ):
        prep_resp = await test_client.post("/api/coach/prep", json={"job_id": job["id"]})

    session_id = prep_resp.json()["session_id"]

    mock_summary = {
        "session_id": session_id,
        "overall_score": 0.72,
        "summary": "Strong fundamentals. Review system design patterns.",
        "areas_to_improve": ["system design", "distributed systems"],
    }

    with patch(
        "jobforce.routers.coach.get_session_summary_data",
        new_callable=AsyncMock,
        return_value=mock_summary,
    ):
        resp = await test_client.get(f"/api/coach/sessions/{session_id}/summary")

    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
    assert "areas_to_improve" in data
    assert isinstance(data["areas_to_improve"], list)
    assert 0.0 <= data["overall_score"] <= 1.0
