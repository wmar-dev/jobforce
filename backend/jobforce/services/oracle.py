"""Oracle service — rank job listings by fit against user profile using Claude."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from anthropic.types import TextBlock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jobforce.db.models import JobListing, UserProfile

logger = logging.getLogger(__name__)


def _extract_text(message: anthropic.types.Message) -> str:
    for block in message.content:
        if isinstance(block, TextBlock):
            return block.text
    return "{}"


_ACTIVE_STATUSES = ("saved", "applied", "interviewing")
_SPARSE_THRESHOLD = 100  # chars — descriptions shorter than this get a warning


def _confidence_label(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


async def rank_jobs(
    session: AsyncSession,
    job_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Score job listings against the user profile.

    Returns a list of result dicts sorted by score descending:
      {job_id, score, confidence, rationale, warning}
    """
    # Load user profile
    profile_result = await session.execute(select(UserProfile).where(UserProfile.id == 1))
    profile = profile_result.scalar_one_or_none()

    profile_text = _build_profile_text(profile)

    # Load jobs to rank
    stmt = select(JobListing)
    if job_ids:
        stmt = stmt.where(JobListing.id.in_(job_ids))
    else:
        stmt = stmt.where(JobListing.status.in_(_ACTIVE_STATUSES))

    jobs_result = await session.execute(stmt)
    jobs = jobs_result.scalars().all()

    if not jobs:
        return []

    results: list[dict[str, Any]] = []
    client = anthropic.AsyncAnthropic()

    for job in jobs:
        description = (job.description or "").strip()
        is_sparse = len(description) < _SPARSE_THRESHOLD
        warning: str | None = None

        if is_sparse:
            warning = "Job description is too sparse for reliable scoring"

        prompt = _build_ranking_prompt(profile_text, job, description)

        try:
            message = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = _extract_text(message)
            parsed = _parse_ranking_response(raw)
        except Exception as exc:
            logger.warning("Oracle ranking failed for job %d: %s", job.id, exc)
            parsed = {"score": 0.0, "rationale": f"Ranking error: {exc}"}

        score = float(parsed.get("score", 0.0))
        score = max(0.0, min(1.0, score))
        confidence = _confidence_label(score) if not is_sparse else "low"
        rationale = parsed.get("rationale", "")

        # Persist scores to job listing
        job.fit_score = score
        job.fit_scored = 1
        job.fit_confidence = confidence
        job.fit_rationale = rationale

        results.append(
            {
                "job_id": job.id,
                "score": score,
                "confidence": confidence,
                "rationale": rationale,
                "warning": warning,
            }
        )

    await session.commit()

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def _build_profile_text(profile: UserProfile | None) -> str:
    if profile is None:
        return "No profile set up yet."
    parts: list[str] = []
    if profile.full_name:
        parts.append(f"Name: {profile.full_name}")
    if profile.headline:
        parts.append(f"Headline: {profile.headline}")
    if profile.skills:
        parts.append(f"Skills: {profile.skills}")
    if profile.experience:
        parts.append(f"Experience: {profile.experience}")
    if profile.preferences:
        parts.append(f"Preferences: {profile.preferences}")
    return "\n".join(parts) if parts else "No profile details provided."


def _build_ranking_prompt(profile_text: str, job: JobListing, description: str) -> str:
    return f"""You are Oracle, a job fit scoring agent. Score how well this job matches the candidate profile.

## Candidate Profile
{profile_text}

## Job Listing
Title: {job.title}
Location: {job.location or "Not specified"}
Role Type: {job.role_type or "Not specified"}
Description: {description or "No description provided."}

## Instructions
Return a JSON object with exactly these fields:
- "score": float between 0.0 (no fit) and 1.0 (perfect fit)
- "rationale": 1-2 sentence explanation of the score

Respond ONLY with valid JSON, no additional text.
Example: {{"score": 0.75, "rationale": "Strong Python background matches required skills."}}"""


def _parse_ranking_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    # Extract JSON if wrapped in markdown code blocks
    if "```" in raw:
        lines = raw.split("\n")
        json_lines = [line for line in lines if line.strip() not in ("```json", "```", "")]
        raw = "\n".join(json_lines)
    try:
        result: dict[str, Any] = json.loads(raw)
        return result
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse Oracle response: %r", raw)
        return {"score": 0.0, "rationale": "Unable to parse ranking response"}
