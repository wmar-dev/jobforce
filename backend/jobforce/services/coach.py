"""Coach service — generate interview prep packs using Claude and web search."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from anthropic.types import TextBlock
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import InterviewSession, JobListing

logger = logging.getLogger(__name__)


async def generate_prep_pack(
    session: AsyncSession,
    job_id: int,
) -> dict[str, Any]:
    """Generate a categorized interview prep pack for a job listing."""
    job = await session.get(JobListing, job_id)
    if job is None:
        raise ValueError(f"Job listing {job_id} not found")

    description = (job.description or "").strip()
    is_technical = _is_technical_role(job.title, description)

    prompt = _build_prep_prompt(job.title, description, is_technical)

    client = anthropic.AsyncAnthropic()

    questions: list[dict[str, Any]] = []

    try:
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = next((b.text for b in message.content if isinstance(b, TextBlock)), "[]")
        questions = _parse_questions_response(raw)
    except Exception as exc:
        logger.warning("Coach prep generation failed: %s", exc)
        questions = _fallback_questions(job.title, is_technical)

    # Store as InterviewSession in DB
    interview = InterviewSession(
        job_listing_id=job_id,
        session_type="prep",
        questions=json.dumps(questions),
    )
    session.add(interview)
    await session.commit()
    await session.refresh(interview)

    return {
        "session_id": interview.id,
        "job_id": job_id,
        "questions": questions,
    }


async def evaluate_answer(
    session: AsyncSession,
    session_id: int,
    question_id: str,
    answer: str,
) -> dict[str, Any]:
    """Evaluate a user's answer to an interview question."""
    interview = await session.get(InterviewSession, session_id)
    if interview is None:
        raise ValueError(f"Interview session {session_id} not found")

    questions: list[dict[str, Any]] = json.loads(interview.questions)
    question = next((q for q in questions if q.get("id") == question_id), None)

    if question is None:
        raise ValueError(f"Question {question_id} not found in session {session_id}")

    prompt = f"""You are Coach, an interview feedback agent.

## Question
Category: {question["category"]}
Question: {question["text"]}

## Candidate's Answer
{answer}

## Instructions
Return a JSON object with:
- "feedback": 2-3 sentence constructive feedback
- "score": float 0.0-1.0

Respond ONLY with valid JSON."""

    client = anthropic.AsyncAnthropic()

    try:
        message = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = next((b.text for b in message.content if isinstance(b, TextBlock)), "{}")
        parsed = _parse_json_response(raw)
    except Exception as exc:
        logger.warning("Answer evaluation failed: %s", exc)
        parsed = {"feedback": "Could not evaluate answer.", "score": 0.0}

    return {
        "question_id": question_id,
        "feedback": parsed.get("feedback", ""),
        "score": float(parsed.get("score", 0.0)),
    }


async def get_session_summary_data(
    session: AsyncSession,
    session_id: int,
) -> dict[str, Any]:
    """Return overall session summary — requires answers to have been recorded."""
    interview = await session.get(InterviewSession, session_id)
    if interview is None:
        raise ValueError(f"Interview session {session_id} not found")

    summary_text = interview.overall_summary or ""

    if summary_text:
        try:
            result: dict[str, Any] = json.loads(summary_text)
            return result
        except (json.JSONDecodeError, ValueError):
            pass

    return {
        "session_id": session_id,
        "overall_score": 0.0,
        "summary": "No answers submitted yet.",
        "areas_to_improve": [],
    }


def _is_technical_role(title: str, description: str) -> bool:
    tech_keywords = (
        "engineer",
        "developer",
        "architect",
        "sre",
        "devops",
        "backend",
        "frontend",
        "fullstack",
        "data",
        "ml",
        "ai",
        "software",
    )
    combined = (title + " " + description).lower()
    return any(kw in combined for kw in tech_keywords)


def _build_prep_prompt(title: str, description: str, is_technical: bool) -> str:
    categories = ["behavioral", "role_specific"]
    if is_technical:
        categories += ["coding", "system_design"]

    return f"""You are Coach, an interview preparation specialist.

## Job
Title: {title}
Description: {description or "Not provided"}

## Instructions
Generate interview questions covering these categories: {", ".join(categories)}

For coding questions: always include a real LeetCode URL.
For behavioral questions: reference real interview sources like Glassdoor when appropriate.

Return a JSON array of question objects. Each question object must have:
- "id": unique string (q1, q2, etc.)
- "category": one of {json.dumps(categories)}
- "text": the interview question
- "source_url": URL where this question was seen (or null)
- "leetcode_url": LeetCode problem URL for coding questions (or null)
- "guidance": brief preparation tip

Generate at least one question per category.
Respond ONLY with a valid JSON array, no additional text."""


def _parse_questions_response(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(line for line in lines if line.strip() not in ("```json", "```", ""))
    try:
        result: list[dict[str, Any]] = json.loads(raw)
        return result
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse coach questions response")
        return []


def _parse_json_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if "```" in raw:
        lines = raw.split("\n")
        raw = "\n".join(line for line in lines if line.strip() not in ("```json", "```", ""))
    try:
        result: dict[str, Any] = json.loads(raw)
        return result
    except (json.JSONDecodeError, ValueError):
        return {}


def _fallback_questions(title: str, is_technical: bool) -> list[dict[str, Any]]:
    questions = [
        {
            "id": "q_behavioral_1",
            "category": "behavioral",
            "text": "Tell me about a time you had to deal with a difficult team member.",
            "source_url": None,
            "leetcode_url": None,
            "guidance": "Use the STAR method: Situation, Task, Action, Result",
        },
        {
            "id": "q_role_1",
            "category": "role_specific",
            "text": f"What experience do you have relevant to this {title} role?",
            "source_url": None,
            "leetcode_url": None,
            "guidance": "Connect your experience directly to the job requirements",
        },
    ]
    if is_technical:
        questions += [
            {
                "id": "q_coding_1",
                "category": "coding",
                "text": "Implement a function to reverse a linked list.",
                "source_url": None,
                "leetcode_url": "https://leetcode.com/problems/reverse-linked-list/",
                "guidance": "Consider iterative vs recursive approaches",
            },
            {
                "id": "q_system_1",
                "category": "system_design",
                "text": "Design a simple rate limiter.",
                "source_url": None,
                "leetcode_url": None,
                "guidance": "Consider token bucket vs leaky bucket algorithms",
            },
        ]
    return questions
