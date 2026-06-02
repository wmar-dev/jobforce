# Research: Coach Skill Migration

## Decision 1: How the skill posts questions to the backend

**Decision**: The skill calls `POST /api/coach/prep` with `job_id` + a pre-formed `questions` array in the request body. The backend stores it and returns `session_id`.

**Rationale**: Reuses the existing endpoint and `InterviewSession` table with minimal change. The frontend already calls this endpoint and reads the response — no frontend changes needed.

**Alternatives considered**:
- New endpoint `POST /api/coach/sessions` (direct session creation) — rejected; unnecessary duplication of route.
- Skill writes directly to SQLite — rejected; bypasses the API layer and breaks the architecture contract.

---

## Decision 2: Shape of the updated `PrepRequest` body

**Decision**: `PrepRequest` gains an optional `questions` field (`list[QuestionItem] | None = None`). When present, the backend skips AI generation entirely and stores the provided questions. When absent (legacy path, kept for backward compat during transition), the backend returns a 400 rather than calling the SDK.

**Rationale**: Makes the new path explicit and testable. The old SDK-calling code is removed, not guarded behind a flag.

**Alternatives considered**:
- Keep `job_id`-only request and move question generation to a separate helper — rejected; adds indirection with no benefit.
- Two separate endpoints — rejected; more surface area, same result.

---

## Decision 3: What happens to answer evaluation (`POST /coach/sessions/{id}/answer`)

**Decision**: The endpoint is kept but the `evaluate_answer` service function is simplified to return a static stub response (`"feedback": "Submit answers via mock interview mode.", "score": 0.0`). No SDK call.

**Rationale**: The frontend `MockInterviewPanel` calls this endpoint; removing it would break the UI. Stubbing preserves the contract while eliminating the SDK call. This is explicitly out of scope per the spec.

**Alternatives considered**:
- Delete the endpoint — rejected; breaks frontend without frontend changes.
- Move answer eval to a skill — deferred; out of scope for this feature.

---

## Decision 4: Question bank strategy in the skill

**Decision**: The skill embeds a curated static bank of questions per category (behavioral, role-specific, coding, system design), then uses in-context Claude reasoning to select and supplement with role-specific questions based on the job title/description fetched from `GET /api/jobs/{id}`.

**Rationale**: Static bank ensures quality LeetCode URLs and STAR-method tips without relying on Claude hallucinating URLs. In-context reasoning adds job-specific questions on top.

**Alternatives considered**:
- Fully dynamic generation (no static bank) — rejected; LeetCode URLs are hallucinated by Claude in practice.
- Fully static (no Claude reasoning) — rejected; loses the job-tailoring value.

---

## Decision 5: Removing the `anthropic` Python package

**Decision**: Remove `anthropic>=0.105.0` from `backend/pyproject.toml` and run `uv sync` to regenerate the lockfile. The `services/coach.py` import is deleted.

**Rationale**: Satisfies the constitution gate (`grep -r "import anthropic" backend/` → zero results) and reduces the dependency surface.

**Alternatives considered**:
- Keep the package but never import it — rejected; constitution gate checks imports, not installs, but keeping an unused dep is pointless.
