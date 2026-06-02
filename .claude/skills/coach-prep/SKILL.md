---
name: coach-prep
description: Generate a Claude Code–powered interview prep pack for a specific job listing (no API key required). Searches the web for company- and role-specific interview questions, then reasons in-context to build a tailored prep pack saved to the backend.
argument-hint: "<job_id>"
user-invocable: true
---

# Coach Prep — Interview Preparation Skill

Generate a tailored interview prep pack by searching the web for real interview questions asked at the company and for the role type, then reasoning in-context to curate and supplement them. No Anthropic API key required in the backend.

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

### 3. Search the web for real interview questions

Run **all searches in parallel** using the WebSearch tool. Use the actual company name and role title from the job data.

**Always run:**
- `"<company name>" interview questions site:glassdoor.com`
- `"<company name>" "<role title>" interview questions`
- `"<company name>" behavioral interview questions`

**For technical roles, also run:**
- `"<company name>" coding interview questions leetcode`
- `"<company name>" system design interview questions`
- `"<role title>" machine learning engineer interview questions` (adapt to actual title)

Then **fetch the top 1–2 most relevant URLs** from the search results using WebFetch to get actual question content. Prioritize Glassdoor, Blind, LeetCode Discuss, levels.fyi, and engineering blogs.

### 4. Synthesize questions from search + in-context reasoning

Using all gathered search results plus the full job description, generate a curated question set. Assign sequential IDs (q1, q2, …).

**Always include: behavioral + role_specific**
**For technical roles also include: coding + system_design**

Guidelines per category:

**Behavioral (at least 4 questions):**
- Prioritize questions that surfaced in search results for this specific company
- Tailor each question to the culture signals in the JD (e.g. "ships fast", "eval-minded", "zero-to-one")
- Write guidance that connects the question to what THIS company is looking for

**Coding (technical roles, at least 3–4 questions):**
- If search results surface specific problems asked at this company, use those
- For each coding question, find the matching LeetCode problem URL (search if needed)
- Write guidance that ties the problem to the role's tech stack or scale requirements

**System Design (technical roles, at least 2–3 questions):**
- Prefer questions that map directly to what the company actually builds (their product, scale, domain)
- Generic SD questions (URL shortener, rate limiter) are fine as fallbacks, but job-specific ones are better

**Role-Specific (at least 3–4 questions):**
- Draw from the JD's "What You'll Do" and "Who You Are" sections
- Each question should probe a specific responsibility or trait called out in the JD
- Guidance should reference the JD language directly (quote phrases) so the answer can mirror it back

### 5. POST to backend to persist the session

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
      "source_url": "<url where this question was found, or null>",
      "leetcode_url": null,
      "guidance": "..."
    },
    ...
  ]
}
```

Set `source_url` to the page URL where a question was found (Glassdoor, Blind, etc.) — this gives provenance. Set `leetcode_url` for coding questions.

Capture `session_id` from the response.

### 6. Display prep pack

Format output grouped by category:

```
🎯 Interview Prep Pack — <Company> · <Title> (Job #<id>)
Session #<session_id> saved — open http://localhost:3000/coach to study in the web UI

Sources searched: <list URLs fetched>

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
- Search results vary by company — smaller or newer companies may have sparse coverage; supplement with JD-derived questions in that case
- The session is saved to the database and will appear in the web UI at http://localhost:3000/coach
- For non-technical roles, coding and system design sections are omitted
- `source_url` in the output gives provenance for each question — useful for following up on the original thread
