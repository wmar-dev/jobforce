# Quickstart: Site Adapter Skill

**Feature**: `004-site-adapter-skill` | **Date**: 2026-05-27

## Prerequisites

1. Playwright MCP server configured in Claude Code:
   ```bash
   claude mcp list   # should show "playwright"
   # If missing:
   claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest
   ```

2. Working git repository with a clean `chrome-extension/content.js`
   (no uncommitted changes to that file).

## Run the skill

```
/site-adapter-update https://openai.com/careers/software-engineer-ad-formats-san-francisco/
```

Claude will:
1. Navigate to the URL in a headless browser.
2. Print a field summary showing every extractable value.
3. Check that `content.js` has no uncommitted edits.
4. Write the adapter to `content.js`.
5. Print a completion report listing which fields are site-specific vs. generic.

## Verify the adapter

1. Open Chrome → `chrome://extensions` → enable Developer Mode.
2. Click **Load unpacked** → select `chrome-extension/`.
3. Navigate to the job posting URL.
4. Click the Jobforce Scout extension icon.
5. Confirm the captured job shows the correct title, company, location, and description.

## Run against a different job board

```
/site-adapter-update https://boards.greenhouse.io/example/jobs/12345
```

Each hostname gets its own adapter entry in `ADAPTERS`. Running for a new
hostname never touches existing entries.

## Reliable selector patterns (discovered during implementation)

- **Title**: `main h2` — OpenAI and many custom career sites use `h2` not `h1` for the job title.
- **Location**: `main h2 + p` — the paragraph immediately after the title heading reliably contains dept + location on OpenAI pages.
- **Compensation**: scan `main p` for any text matching `$NNN` — works across sites that surface salary in the body rather than a dedicated element.
- **Description**: `main article` or `main section` — prefer semantic wrappers over class-name selectors.
- **Fragile patterns to avoid**: nth-child selectors, class names containing random hashes, deeply nested div chains.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `❌ Could not load URL` | Check that the URL is publicly accessible (no login) |
| `⚠️ content.js has uncommitted changes` | `git stash` or commit before running the skill |
| Fields show "(not found)" | The page may use JavaScript rendering — retry once |
| Adapter writes but fields wrong | Re-run the skill; the updated adapter replaces the old one |
| Compensation shows full paragraph text | Selector is too broad — tighten to the element containing only the salary range |
