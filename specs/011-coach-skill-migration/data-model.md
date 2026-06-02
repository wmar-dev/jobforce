# Data Model: Coach Skill Migration

## Unchanged entities

### InterviewSession (no schema change)

| Field            | Type        | Notes                                      |
| ---------------- | ----------- | ------------------------------------------ |
| id               | int PK      | Auto-increment                             |
| job_listing_id   | int FK      | Cascade delete from JobListing             |
| session_type     | str         | CHECK IN ('prep', 'mock')                  |
| questions        | TEXT (JSON) | Array of QuestionItem objects              |
| overall_summary  | TEXT (JSON) | Nullable; not written by this feature      |
| created_at       | datetime    |                                            |
| updated_at       | datetime    |                                            |

No migration required — the table schema is identical.

### QuestionItem (JSON shape, no change)

| Field        | Type          | Notes                              |
| ------------ | ------------- | ---------------------------------- |
| id           | str           | e.g. "q1", "q_behavioral_1"       |
| category     | str           | behavioral / coding / system_design / role_specific |
| text         | str           | The question text                  |
| source_url   | str or null   |                                    |
| leetcode_url | str or null   | Required for coding category       |
| guidance     | str or null   | Preparation tip                    |

## Changed: PrepRequest (backend Pydantic model)

**Before**:
```python
class PrepRequest(BaseModel):
    job_id: int
```

**After**:
```python
class PrepRequest(BaseModel):
    job_id: int
    questions: list[QuestionIn]  # required; skill always provides this
```

Adding `questions` as required means the backend no longer needs to generate questions itself. The skill is now the sole producer.

## Removed: coach service SDK functions

| Function              | Disposition                                         |
| --------------------- | --------------------------------------------------- |
| `generate_prep_pack`  | Removed; replaced by skill + simplified store-only logic in router |
| `evaluate_answer`     | Simplified to stub (no SDK call)                    |
| `get_session_summary_data` | Kept as-is (reads DB, no SDK)                 |
| `_is_technical_role`  | Moved to skill (SKILL.md inline logic)              |
| `_build_prep_prompt`  | Removed (prompt lives in skill)                     |
| `_parse_questions_response` | Removed                                       |
| `_fallback_questions` | Removed (static bank lives in skill)                |
