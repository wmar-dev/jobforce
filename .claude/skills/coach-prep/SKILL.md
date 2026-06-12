---
name: coach-prep
description: Generate a Claude Code–powered interview prep pack for a specific job listing (no API key required). Searches the web for company- and role-specific interview questions, then reasons in-context to build a tailored prep pack saved to the backend.
argument-hint: "<job_id>"
user-invocable: true
---

# Coach Prep — Interview Preparation Skill

Generate a tailored interview prep pack by searching the web for real interview questions asked at the company and for the role type, then reasoning in-context to curate and supplement them. No Anthropic API key required in the backend. The session loads automatically when a job is selected in the web UI.

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

Then **fetch 3–4 URLs from at least 3 different domains** across the search results using WebFetch to get actual question content.

**Prefer first-hand candidate reports**: Glassdoor, Blind (teamblind.com), Reddit, 1point3acres, LeetCode Discuss, levels.fyi, and company engineering blogs. These reflect real interview experiences.

**Deprioritize content-marketing/SEO sites** whose "interview questions" posts are AI-written summaries rather than sourced from real candidates — e.g. interviewcoder.co, prepfully.com, vervecopilot.com, companyinterviews.com, prachub.com. Only fall back to these if no first-hand sources surface for a given company.

**Source diversity is required**: do not cite the same `source_url` for more than ~half the questions in any one category, and never for every question in the full set. If a single page yields several good questions, still pull at least one more question from a different domain for that category. If search results keep returning the same 1-2 domains, run an additional targeted search (e.g. add `site:teamblind.com` or `site:1point3acres.com`) before settling.

**Do NOT WebFetch or construct leetcode.com URLs** — LeetCode requires JavaScript to render (WebFetch returns nothing useful), and slug guessing produces "Page Not Found" errors because LeetCode slugs don't always match the problem title. Instead, for each coding problem, run a WebSearch for `site:leetcode.com/problems "<problem title>"` and use the URL directly from the search result. Only set `leetcode_url` when you have a URL from search results — never construct one yourself.

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
- Only include problems you found by name in search results (e.g. from a Glassdoor/Blind thread listing what was asked) — do NOT invent problem names
- Pull problems from at least 2 different source pages — do not cite the same `source_url` for every coding question, even if one page lists multiple problems
- For each problem name found, run `site:leetcode.com/problems "<problem name>"` via WebSearch; use the URL only if a result comes back with a matching leetcode.com/problems/ URL — omit `leetcode_url` entirely if no result is found
- Never construct or guess a LeetCode URL — only use URLs that appeared verbatim in search results
- System design topics (rate limiter, URL shortener, etc.) are NOT LeetCode problems; put them in system_design category, never assign a `leetcode_url`
- Write guidance that ties the problem to the role's tech stack or scale requirements

**System Design (technical roles, at least 2–3 questions):**
- Prefer questions that map directly to what the company actually builds (their product, scale, domain)
- Generic SD questions (URL shortener, rate limiter) are fine as fallbacks, but job-specific ones are better

**Role-Specific (at least 3–4 questions):**
- Draw from the JD's "What You'll Do" and "Who You Are" sections
- Each question should probe a specific responsibility or trait called out in the JD
- Guidance should reference the JD language directly (quote phrases) so the answer can mirror it back

### 5. POST to backend to persist the session

Write the full JSON payload to a temp file (e.g. `/tmp/coach_<job_id>.json`) and POST it with curl to avoid shell quoting issues with apostrophes and special characters in question text:

```bash
# Write payload to temp file first
# Then POST, extracting just the session_id to avoid echoing the full payload back:
curl -s -X POST http://localhost:8000/api/coach/prep \
  -H "Content-Type: application/json" \
  -d @/tmp/coach_<job_id>.json | jq -r '.session_id'
```

Set `source_url` to the page URL where a question was found (Glassdoor, Blind, etc.) — this gives provenance. Set `leetcode_url` for coding questions only when you have a URL from search results.

### 6. Confirm completion

Output a single line:

```
✅ Session #<session_id> saved — http://localhost:3000/coach?job=<job_id>
```

Do not print the questions — they are in the UI.

## Notes

- Backend must be running: `make dev` from repo root (or `cd backend && make dev`)
- Search results vary by company — smaller or newer companies may have sparse coverage; supplement with JD-derived questions in that case
- The session is saved to the database and will appear in the web UI at http://localhost:3000/coach
- For non-technical roles, coding and system design sections are omitted
- `source_url` in the output gives provenance for each question — useful for following up on the original thread
