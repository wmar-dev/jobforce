---
name: coach-prep
description: Generate a Claude Code–powered interview prep pack for a specific job listing (no API key required). Fetches job details, reasons about role-specific questions in-context, and saves the session to the backend so it appears in the web UI.
argument-hint: "<job_id>"
user-invocable: true
---

# Coach Prep — Interview Preparation Skill

Generate a tailored interview prep pack using in-context Claude reasoning. No Anthropic API key required in the backend — questions are generated here in Claude Code (Pro subscription) and saved to the database.

## Usage

```
/coach-prep <job_id>
```

## Steps

### 1. Fetch job details

```
GET http://localhost:8000/api/jobs/<job_id>
```

Extract: `title`, `description`, `company.name`. If 404, stop with error.

### 2. Detect role type

Mark as **technical** if the title (lowercased) contains any of:
`engineer`, `developer`, `architect`, `sre`, `devops`, `backend`, `frontend`, `fullstack`, `data`, `ml`, `ai`, `software`

### 3. Generate questions using the curated bank below + in-context reasoning

Start from the static bank, then **supplement with 2–4 job-specific questions** based on the actual title and description. Assign sequential IDs (q1, q2, …).

Always include: **behavioral** + **role_specific**
For technical roles also include: **coding** + **system_design**

#### Static Question Bank

**Behavioral** (always include at least 3):

| id | text | guidance |
|----|------|----------|
| b1 | Tell me about a time you led a project under significant time or resource pressure. | STAR method: Situation, Task, Action, Result. Quantify the outcome. |
| b2 | Describe a situation where you disagreed with a technical decision made by your team. How did you handle it? | Focus on constructive disagreement — show you can influence without authority. |
| b3 | Tell me about a time a project you owned failed or fell short. What did you learn? | Demonstrate ownership and self-awareness. Avoid blaming others. |
| b4 | Describe a time you had to pick up an unfamiliar technology or domain quickly to deliver something. | Show learning agility. Mention the ramp-up strategy and the result. |

**Coding** (technical roles only, always include at least 3 with LeetCode URLs):

| id | text | leetcode_url | guidance |
|----|------|-------------|----------|
| c1 | Implement an LRU Cache with O(1) get and put operations. | https://leetcode.com/problems/lru-cache/ | Use OrderedDict or a doubly-linked list + hashmap. For Staff/Senior level: discuss thread-safety and distributed caching. |
| c2 | Given a string, determine if it has valid parentheses (all brackets properly opened and closed). | https://leetcode.com/problems/valid-parentheses/ | Use a stack. Edge case: empty string is valid. |
| c3 | Given an array of integers, return indices of the two numbers that add up to a target. | https://leetcode.com/problems/two-sum/ | Single-pass hashmap. Discuss time/space tradeoffs. |
| c4 | Merge a list of overlapping intervals and return the merged result. | https://leetcode.com/problems/merge-intervals/ | Sort by start time first. Watch for edge cases where intervals share an endpoint. |
| c5 | Design and implement a hit counter that counts hits in the last 5 minutes. | https://leetcode.com/problems/design-hit-counter/ | Queue-based or sliding window. Extend to distributed counter with Redis. |

**System Design** (technical roles only, always include at least 2):

| id | text | guidance |
|----|------|----------|
| s1 | Design a distributed rate limiter that enforces per-user API quotas across multiple servers. | Token bucket or sliding window. Discuss Redis + Lua scripts for atomic enforcement, and failure modes. |
| s2 | Design a URL shortener service (like bit.ly) with high availability and low read latency. | Hash generation, collision handling, read-path caching, and DB schema. Discuss trade-offs between base62 encoding and MD5/SHA. |
| s3 | Design a notification delivery system that sends millions of push notifications per day. | Fan-out strategies (per-send vs. pre-compute), priority queues, dead-letter queues, and delivery guarantees. |

**Role-Specific** (always include at least 2, tailored to title):

| id | text | guidance |
|----|------|----------|
| r1 | What's the most complex system you've built end-to-end? Walk me through the key design decisions. | Pick a system that shows breadth. Discuss trade-offs you made, what you'd change in hindsight. |
| r2 | How do you approach debugging a production issue with incomplete information under time pressure? | Show your systematic process: observe, hypothesize, isolate, fix, verify. Mention tooling (logs, traces, metrics). |

### 4. POST to backend to persist the session

```
POST http://localhost:8000/api/coach/prep
Content-Type: application/json

{
  "job_id": <job_id>,
  "questions": [
    {
      "id": "q1",
      "category": "behavioral",
      "text": "...",
      "source_url": null,
      "leetcode_url": null,
      "guidance": "..."
    },
    ...
  ]
}
```

Capture `session_id` from the response.

### 5. Display prep pack

Format output grouped by category:

```
🎯 Interview Prep Pack — <Company> · <Title> (Job #<id>)
Session #<session_id> saved — open http://localhost:3000/coach to study in the web UI

💬 Behavioral (<N> questions):

Q1: <question text>
    Tip: <guidance>

...

💻 Coding (<N> questions):   [technical roles only]

Q1: <question text>
    LeetCode: <url>
    Tip: <guidance>

...

🏗️ System Design (<N> questions):   [technical roles only]

Q1: <question text>
    Tip: <guidance>

...

🎯 Role-Specific (<N> questions):

Q1: <question text>
    Tip: <guidance>

...

─────────────────────────────────
Total: <N> questions  |  LeetCode links: <N>
Session #<session_id> persisted to backend
```

## Notes

- Backend must be running: `make dev` from repo root (or `cd backend && make dev`)
- Questions are generated fresh each time using in-context Claude reasoning — no API key required in the backend
- The session is saved to the database and will appear in the web UI at http://localhost:3000/coach
- For non-technical roles, coding and system design sections are omitted
