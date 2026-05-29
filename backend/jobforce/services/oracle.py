"""Oracle service — job fit scoring helpers.

AI ranking is performed by Claude Code via the /oracle-rank skill.
This module retains helper functions for prompt formatting reference
and confidence label derivation. The rank_jobs() function that called
the Anthropic SDK has been removed (Constitution Principle VI).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from jobforce.db.models import JobListing, Resume

logger = logging.getLogger(__name__)


_SPARSE_THRESHOLD = 100  # chars — descriptions shorter than this get a warning


def _confidence_label(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _build_profile_text(resume: Resume | None) -> str:
    if resume is None:
        return "No resume configured."
    try:
        data: dict[str, Any] = json.loads(resume.structured_data)
    except (json.JSONDecodeError, ValueError):
        return "Resume data could not be read."
    return json.dumps(data, indent=2)


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
