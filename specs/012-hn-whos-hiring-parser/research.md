# Research: Hacker News "Who's Hiring" Parser

## HN HTML Structure

### Decision: Two distinct page layouts to handle

**Single comment page** (`item?id=<comment-id>` where the ID is a comment, not the thread):
- The target comment is inside `table.fatitem > tr.athing > td.default > div.comment > div.commtext`
- No `tr.athing.comtr` rows — the `.commtext` element is the only one
- `source_url` = `https://news.ycombinator.com/item?id=<comment-id>` (from URL)
- Comment ID = from URL query param `id`

**Thread page** (`item?id=<thread-id>`):
- All comments are in `tr.athing.comtr` rows
- Top-level comments have `td.ind[indent="0"]`
- Each comment's ID is in `tr.athing.comtr[id]` attribute
- Used by `hn_thread` CLI to extract comment URLs

**Rationale**: `scout_fetch` fetches the single-comment URL; the adapter handles the `.fatitem` layout. The `hn_thread` CLI fetches the thread URL and extracts top-level `tr.athing.comtr[id]` values.

**Alternatives considered**: Anchored thread URL (`item?id=<thread>#<comment-id>`) — rejected because HN does not serve a page scoped to one comment at a hash anchor; you get the full thread. Using `item?id=<comment-id>` is the canonical single-comment URL.

---

## Pipe-Delimited First-Line Convention

### Decision: Parse only when `|` present in first line; positions 0–3 map to company/title/location/extras

**Observed format** (from live thread sampling):
```
Company | Role | Location | Remote/Hybrid | Employment Type [| optional extras]
```

Real examples:
- `Climate Friendly | Senior Data Engineer | Sydney, Melbourne, Brisbane (Australia) | Hybrid | Full Time`
- `Hotwash | Founding Engineer (→ CTO for the right person) | REMOTE (US), Boston a plus | Full-time`
- `Zulip | Senior Backend/Infrastructure Engineer | REMOTE | Full-time |`
- `Aquabyte | USA | Full-Time | Perception Engineer | Platform Engineer | SF HYBRID and REMOTE`

**Position mapping**:
- `tokens[0]` → `company_name` (always)
- `tokens[1]` → `title` (usually; occasionally location if company puts location second)
- `tokens[2]` → `location` (usually; scan all tokens for known location/remote keywords as fallback)
- Remaining tokens → scan for `full-time`, `part-time`, `contract`, `remote`, `onsite`, `hybrid`

**Role type detection**: scan all pipe tokens (lowercased) for `full-time`/`full time` → `full-time`, `part-time` → `part-time`, `contract` → `contract`, `intern` → `internship`. Fall back to existing `_generic_role_type` body scan.

**Rationale**: Position 0 is always the company name in observed data. Position 1 is almost always the role. Scanning all tokens for role-type keywords is more robust than positional for employment type.

---

## Dead/Flagged Comment Detection

### Decision: Check `.commtext` class for `cdd` (dead) or absence of text

**Rationale**: Live thread inspection found no dead comments in the June 2026 thread, but HN's CSS classes for dead comments are `cdd` (dead) and `cdf` (flagged). A comment with no `.commtext` or with `cdd`/`cdf` class should be skipped by `hn_thread` CLI.

**Implementation**: In `hn_thread`, skip any `tr.athing.comtr` where `.commtext` is absent or has class `cdd` or `cdf`.

---

## `hn_thread` CLI: HTTP vs Playwright

### Decision: Plain HTTP fetch (httpx or urllib) — no Playwright

**Rationale**: HN is fully server-rendered HTML. The thread page with all top-level comments loads without JavaScript. `scout_fetch` uses Playwright for JS-heavy SPAs; HN does not need it. Plain HTTP is faster, simpler, and avoids the Playwright dependency for this module.

**User-Agent required**: HN returns `<body>Sorry.</body>` to requests without a User-Agent header. Set `User-Agent: Mozilla/5.0` on all requests.

**Alternatives considered**: Playwright (overkill), requests library (not in project deps — use stdlib `urllib.request` to avoid new deps, or httpx which is already used elsewhere).

---

## `hn_thread` Output Format

### Decision: JSON array of comment URL strings to stdout

```json
["https://news.ycombinator.com/item?id=48408037", "https://news.ycombinator.com/item?id=48358328", ...]
```

**Rationale**: Mirrors `scout_fetch` stdout JSON pattern. Simple for the skill to parse with `json.loads`. Count is implicit from array length.

---

## `scout-companies` HN Detection

### Decision: Detect by hostname `news.ycombinator.com` in the careers URL

When `/scout-companies` processes a company entry whose `careers_url` matches `news.ycombinator.com`:
1. Run `python -m jobforce.cli.hn_thread <careers_url>` to get comment URLs as JSON
2. For each URL in the array, run `scout_fetch --url <url>` (existing pipeline)
3. Skip Playwright careers-page navigation (step 4a–4d in current skill) for HN entries

**Rationale**: HN thread URLs are not "careers pages" in the normal sense — there are no job-listing anchor tags to extract. The `hn_thread` CLI handles the extraction deterministically.
