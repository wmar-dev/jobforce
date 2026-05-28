# Site Adapter Update

Inspect a job posting URL using Playwright MCP, extract structured field data,
then generate or update the site-specific adapter in the Chrome extension's
content script.

## Usage

```
/site-adapter-update <url>
```

## Steps

### Step 1: Validate Input

If no URL argument was provided, print:

```
❌ Usage: /site-adapter-update <url>
```

Then stop — do not proceed further.

---

### Step 2: Navigate to the Job Posting

Navigate to the URL using Playwright MCP:

```
mcp__playwright__browser_navigate({ url: "<url>" })
```

If navigation fails or the page returns an error, print:

```
❌ Could not load <url>: <reason>
```

Then stop — do not modify any files.

---

### Step 3: Capture Accessibility Snapshot

Take an accessibility snapshot of the page:

```
mcp__playwright__browser_snapshot()
```

Use the snapshot's YAML element tree to locate field values. Prefer semantic
signals over class names:

- **title**: text of the first `heading[level=1]` or `heading[level=2]` in `main`
- **company_name**: infer from page title, `og:site_name` meta, or known hostname
- **location**: text of the first `paragraph` immediately following the title heading,
  or a paragraph/listitem containing a city name or "Remote"
- **description**: combined text of all `paragraph` elements in the main content
  region (exclude nav, footer, sidebar)
- **compensation**: text of any paragraph containing a `$` sign and digits
  (e.g., "$230K – $385K")
- **role_type**: scan full body text for "full-time", "part-time", "contract",
  or "internship" (case-insensitive); return the first match or null

Extract the hostname from the URL, stripping any `www.` prefix
(e.g., `www.openai.com` → `openai.com`).

Check whether `chrome-extension/content.js` already contains an entry for this
hostname in the `ADAPTERS` object. Set `adapter_exists` to `true` or `false`.

---

### Step 4: Display Field Summary

Print the field summary **before making any changes**:

```
## Field Summary: <hostname>

| Field        | Value                             |
| ------------ | --------------------------------- |
| title        | <value or "(not found)">          |
| company_name | <value or "(not found)">          |
| location     | <value or "(not found)">          |
| description  | <first 200 chars>...              |
| compensation | <value or "(not found)">          |
| role_type    | <value or "(not found)">          |

Adapter exists: <Yes / No>
```

If title **and** company_name are both "(not found)", print:

```
⚠️ This page may not be a job posting — title and company were not found.
   Proceed with writing the adapter anyway? (y/n)
```

Wait for user response. If the user says "n" or "no", stop without writing.

---

### Step 5: Git Guard

Run:

```bash
git diff --name-only chrome-extension/content.js
```

If the command produces any output (the file has uncommitted changes), print:

```
⚠️ chrome-extension/content.js has uncommitted changes.
   Commit or stash them before running this skill.
```

Then stop — do not modify any files.

---

### Step 6: Generate the Site Adapter

Build a JavaScript adapter object for this hostname containing **only** the
fields that were successfully extracted (i.e., not "(not found)"). Omit fields
where the generic adapter already works well enough.

Selector rules:
- Prefer `heading` level selectors (`h1`, `h2`) over class names.
- Prefer sibling relationships (`h2 + p`) over nth-child positions.
- Prefer ARIA roles and `data-*` attributes when available.
- If a selector is fragile (class-based or position-dependent), note it in the
  completion report.

Example output for a new adapter:

```js
const exampleAdapter = {
  company_name: () => "Example Corp",
  title: (doc) => text(doc.querySelector("main h1")) || null,
  location: (doc) => text(doc.querySelector("main h1 + p")) || null,
  compensation: (doc) => {
    for (const el of doc.querySelectorAll("main p")) {
      const t = (el.innerText ?? el.textContent ?? "").trim();
      if (/\$[\d,]+/.test(t)) return t;
    }
    return null;
  },
};
```

---

### Step 7: Update `chrome-extension/content.js`

Read the current contents of `chrome-extension/content.js`.

Locate the `ADAPTERS` object literal (the block starting with
`const ADAPTERS = {`).

**If an entry for this hostname already exists**: replace it in place with the
newly generated adapter object. Do not create a duplicate entry.

**If no entry exists**: insert a new named adapter constant just before the
`/* ─── Registry` comment block, then add the hostname key to the `ADAPTERS`
object.

Leave all other content — the generic adapter, `slugToLocation`,
`runAdapter`, `merge`, the message listener, and the module exports —
completely unchanged.

---

### Step 8: Completion Report

Print:

```
✅ Adapter written for <hostname>
   File: chrome-extension/content.js
   Fields with site-specific extractors: <comma-separated list>
   Fields falling back to generic adapter: <comma-separated list>
   Fragile selectors (if any): <list or "none">
```

---

## Notes

- The Playwright MCP server must be running: `claude mcp list` should show `playwright`.
  If missing: `claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest`
- Pages behind login are not supported — the skill requires a publicly accessible URL.
- Run the skill twice on the same URL to verify idempotency (second run replaces,
  not duplicates, the adapter entry).
- After the adapter is written, reload the extension in Chrome
  (`chrome://extensions` → toggle off/on or click the reload icon) and test
  capture on the target URL.
