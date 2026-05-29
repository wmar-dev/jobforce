# Research: Oracle and Forge Use Resume as Candidate Profile

**Branch**: `007-oracle-forge-resume` | **Date**: 2026-05-28

## Decisions

### 1. Resume as single source of truth for candidate data

**Decision**: Use `Resume` (`is_base=1`) as the sole source of candidate profile data for both oracle ranking and forge tailoring. Remove `UserProfile` entirely.

**Rationale**: `UserProfile` was a sparse free-text precursor to the richer `Resume.structured_data` JSON. Keeping both creates two sources that can drift out of sync. Since `Resume` is strictly richer, the fallback direction is one-way: no resume → low-confidence warning, not a degraded profile.

**Alternatives considered**:
- Keep UserProfile as fallback → Rejected. Two sources of truth for the same concept. Confusing to maintain and document.
- Merge UserProfile fields into Resume schema → Rejected. Unnecessary complexity; Resume structured_data already covers name, skills, experience and more.

---

### 2. Oracle "no resume" behavior: low-confidence warning

**Decision**: When no base resume exists, oracle scores jobs with `confidence: low` and surfaces the warning "No base resume configured" rather than erroring or silently scoring.

**Rationale**: Oracle is always runnable, even without a resume (useful for quick checks). The warning gives the user actionable direction. This matches the existing pattern for sparse job descriptions (< 100 chars → `confidence: low` + warning).

**Alternatives considered**:
- Skip/error the job → Rejected. Too disruptive for a missing-config condition.
- Silent low score → Rejected. User has no signal that something is missing.

---

### 3. Forge AI tailoring moved to Claude Code skill (Constitution VI)

**Decision**: Remove `anthropic` SDK from `services/forge.py`. The `/forge-tailor` skill performs the AI reasoning and POSTs the resulting `structured_data` to `POST /resume/tailor`. The backend stores the result and computes the diff.

**Rationale**: Constitution Principle VI prohibits programmatic SDK/API calls that incur per-token billing. Claude Code subscription covers the same capability. Moving tailoring to the skill is architecturally cleaner: the backend becomes a pure data store, AI logic lives in the skill layer.

**Alternatives considered**:
- Keep SDK call, add cost ceiling → Rejected. Constitution VI is non-negotiable; governance amendment would be required.
- Use a local model → Rejected. Out of scope and over-engineered for a personal tool.

---

### 4. POST /resume/tailor contract change

**Decision**: `POST /resume/tailor` now accepts `{job_id, structured_data}` (skill sends pre-tailored JSON). `base_resume_id` is removed from the request; the backend always diffs against the stored base resume.

**Rationale**: With the skill doing the AI work, the endpoint's only job is to store the result and return the diff. Accepting `base_resume_id` from the caller is redundant — the server already knows which resume is the base.

**Alternatives considered**:
- Keep `base_resume_id` optional for forward-compatibility → Accepted as soft default (field accepted but unused if omitted). Ultimately dropped to keep the contract minimal.
