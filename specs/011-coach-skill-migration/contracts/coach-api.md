# API Contract: Coach Endpoints (post-migration)

## POST /api/coach/prep

Creates an `InterviewSession` from a pre-formed question list provided by the skill.

**Request**:
```json
{
  "job_id": 42,
  "questions": [
    {
      "id": "q1",
      "category": "behavioral",
      "text": "Tell me about a time you led under pressure.",
      "source_url": null,
      "leetcode_url": null,
      "guidance": "Use the STAR method."
    },
    {
      "id": "q2",
      "category": "coding",
      "text": "Implement an LRU cache.",
      "source_url": null,
      "leetcode_url": "https://leetcode.com/problems/lru-cache/",
      "guidance": "Use OrderedDict for O(1) operations."
    }
  ]
}
```

**Response 200**:
```json
{
  "session_id": 7,
  "job_id": 42,
  "questions": [ /* same array echoed back */ ]
}
```

**Response 404**: Job listing not found.

**Change from prior contract**: `questions` is now required in the request body. The backend no longer calls any AI service.

---

## POST /api/coach/sessions/{session_id}/answer

Returns stub feedback. No AI call.

**Request**:
```json
{ "question_id": "q1", "answer": "I led a team of 5 during an outage..." }
```

**Response 200**:
```json
{
  "question_id": "q1",
  "feedback": "Submit answers via mock interview mode.",
  "score": 0.0
}
```

**Note**: Answer evaluation via AI is out of scope. Stub response preserves the frontend contract.

---

## GET /api/coach/sessions/{session_id}/summary

Unchanged from current contract. Returns empty summary if `overall_summary` is null (which it always will be post-migration, since nothing writes it).

**Response 200**:
```json
{
  "session_id": 7,
  "overall_score": 0.0,
  "summary": "No answers submitted yet.",
  "areas_to_improve": []
}
```
