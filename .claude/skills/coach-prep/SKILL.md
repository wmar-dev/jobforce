---
name: coach-prep
description: Generate an AI-powered interview prep pack for a specific job listing. Fetches questions by type (behavioral, coding, system design, role-specific) from the backend and displays them with tips and LeetCode links. Use before an interview.
argument-hint: "<job_id>"
user-invocable: true
---

# Coach Prep — Interview Preparation Skill

Generate an AI-powered interview prep pack for a job listing.

## Usage

```
/coach-prep <job_id>
```

## Steps

1. POST to Coach prep endpoint:
   ```json
   POST http://localhost:8000/api/coach/prep
   {
     "job_id": <job_id>
   }
   ```

2. Display prep pack categorized by type:
   ```
   🎯 Interview Prep Pack — Job #<id>
   
   💬 Behavioral (2 questions):
   
   Q1: Tell me about a time you had to deal with a difficult team member.
       Source: glassdoor.com
       Tip: Use the STAR method — Situation, Task, Action, Result.
   
   Q2: ...
   
   💻 Coding (2 questions):
   
   Q1: Implement a LRU Cache.
       LeetCode: https://leetcode.com/problems/lru-cache/
       Tip: Use OrderedDict for O(1) operations.
   
   🏗️ System Design (1 question):
   
   Q1: Design a distributed rate limiter.
       Tip: Consider Redis + token bucket algorithm.
   
   🎯 Role-Specific (1 question):
   ...
   ```

3. Report summary:
   - Total questions generated
   - LeetCode problems linked

## Notes

- Backend must be running: `cd backend && make dev`
- Questions are generated fresh each time using Claude AI
- Session ID is returned — use it for mock interview answers via POST /api/coach/sessions/{id}/answer
