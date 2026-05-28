# Implementation Plan: Chrome Extension Job Capture — Site Adapter Framework

**Branch**: `003-openai-capture` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**User Input**: have a generic framework that can be extended to multiple websites and formats for capturing job pages through chrome extension.

## Summary

Refactor `content.js` from a single flat extractor into a **site adapter registry**. Each adapter is a small object keyed by hostname that overrides only the fields it knows how to extract. A generic fallback adapter handles all other sites. OpenAI is the first concrete adapter. Adding support for a new site requires adding one object to the registry — no structural changes.

## Technical Context

**Runtime**: Chrome Extension MV3 — content script (`content.js`) runs in page context; no Node.js, no bundler, plain ES2020.

**Existing entry point**: `chrome-extension/content.js` — single `extractJobData()` function.

**Framework pattern**: Adapter registry — `{ hostname → adapter }` map, looked up by `window.location.hostname`, falling back to a `genericAdapter`. Each adapter declares only the fields it can extract; a `merge()` helper fills gaps from the generic result.

**OpenAI page structure** (openai.com/careers/*):

- Title: `<h1>` — present and reliable
- Company: hostname inference (`openai.com` → `"OpenAI"`) — no DOM element
- Location: `<p>` near `<h1>` (`h1 + p` or `h1 ~ p`); also parseable from URL slug last segment
- Description: `<article>` or `<main section>` prose block
- Role type: body text scan (same as generic)

**Constraints**:

- `content.js` MUST remain a single file (no bundler — MV3 content scripts load as plain JS)
- `background.js` and `popup.js` are unchanged
- Existing extraction behavior for non-OpenAI pages MUST NOT regress

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Test-First | ✅ PASS | Jest tests in `chrome-extension/tests/adapters/` — written before implementation |
| II. Code Quality | ✅ PASS | ESLint configured; each adapter function ≤ 10 lines; complexity ≤ 3 |
| III. Self-Improvement Loop | ✅ PASS | Adding a new adapter = one registry entry; framework enforces its own extensibility |
| IV. Simplicity & Clarity | ✅ PASS | Registry is ~5 lines; adapters are pure field extractors with no shared state |
| V. Observability | ✅ PASS | Per-field try/catch logs `[jobforce] adapter field ${key} error` to console |

No violations. No Complexity Tracking entries needed.

## Project Structure

### Files Changed

```text
chrome-extension/
├── content.js                        ← rewrite: adapter registry + generic + openai
└── tests/
    ├── content.test.js               ← existing placeholder (extend with integration test)
    └── adapters/
        ├── generic.test.js           ← NEW: tests for generic extractor
        └── openai.test.js            ← NEW: tests for OpenAI adapter
```

`background.js`, `popup.js`, `manifest.json` — unchanged.

## Phase 0: Research

**Skipped** — no unknowns:

- OpenAI `<h1>` is present when the user manually navigates and clicks the button (React hydration is complete before user interaction)
- Company name is absent from DOM on openai.com/careers — hostname inference is the right approach
- Location appears as plain text in `<p>` immediately after `<h1>`; URL slug is a reliable fallback
- Single-file constraint is acceptable — `content.js` will remain under 120 lines with the framework + 2 adapters

## Phase 1: Design

### Adapter Interface

Each adapter is a plain object with optional field extractor functions:

```js
// Fields any adapter may define — all optional
{
  title:        (doc) => string | null,
  company_name: (doc) => string | null,
  location:     (doc) => string | null,
  description:  (doc) => string | null,
  role_type:    (doc) => string | null,
}
```

A field present in the adapter wins over the generic result. A `null` return defers to the generic value.

### Registry + Merge (the framework)

```js
const ADAPTERS = {
  "openai.com": openaiAdapter,
  // "greenhouse.io": greenhouseAdapter,   // future — add one entry
  // "lever.co": leverAdapter,             // future
};

function extractJobData() {
  const hostname = window.location.hostname.replace(/^www\./, "");
  const adapter  = ADAPTERS[hostname] ?? genericAdapter;
  const base     = runAdapter(genericAdapter, document);
  const override = adapter !== genericAdapter ? runAdapter(adapter, document) : {};
  return { source_url: window.location.href,
           html: document.documentElement.outerHTML,
           ...merge(base, override) };
}
```

`runAdapter` calls each field function inside try/catch; errors produce `null` and log to console.

### Generic Adapter (existing behavior, extracted)

```js
const genericAdapter = {
  title: (doc) =>
    doc.querySelector("h1")?.innerText?.trim() ||
    doc.title?.replace(/\s*[-|].*$/, "").trim() || "",
  company_name: (doc) =>
    doc.querySelector("[data-company], .company-name, .employer-name")
      ?.innerText?.trim() ||
    doc.querySelector('meta[property="og:site_name"]')?.content || "",
  location: (doc) =>
    doc.querySelector("[data-location], .job-location, .location")
      ?.innerText?.trim() ||
    doc.querySelector('meta[name="job:location"]')?.content || null,
  description: (doc) =>
    doc.querySelector('[class*="description"], [class*="job-desc"], #job-description')
      ?.innerText?.trim() || null,
  role_type: (doc) => {
    const t = doc.body?.innerText?.toLowerCase() || "";
    if (t.includes("full-time") || t.includes("full time")) return "full-time";
    if (t.includes("part-time") || t.includes("part time")) return "part-time";
    if (t.includes("contract")) return "contract";
    if (t.includes("internship") || t.includes("intern")) return "internship";
    return null;
  },
};
```

### OpenAI Adapter

```js
function slugToLocation(pathname) {
  const seg = pathname.replace(/\/$/, "").split("/").pop() || "";
  // e.g. "full-stack-software-engineer-applied-foundations-san-francisco"
  // Known city names at end of slug:
  const cities = ["san-francisco", "new-york", "london", "seattle", "remote"];
  const hit = cities.find((c) => seg.endsWith(c));
  return hit ? hit.split("-").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ") : null;
}

const openaiAdapter = {
  company_name: () => "OpenAI",
  location: (doc) =>
    doc.querySelector("h1 + p, h1 ~ p")?.innerText?.trim() ||
    slugToLocation(window.location.pathname) ||
    null,
  description: (doc) =>
    doc.querySelector("article, main section")?.innerText?.trim() || null,
};
```

### Merge Helper

```js
function merge(base, override) {
  const out = { ...base };
  for (const [k, v] of Object.entries(override)) {
    if (v != null && v !== "") out[k] = v;
  }
  return out;
}
```

### Tests

**`tests/adapters/generic.test.js`** — DOM fixtures via `@testing-library/dom` or jsdom:

- Given `<h1>Senior Engineer</h1>`, title = "Senior Engineer"
- Given `<meta property="og:site_name" content="Acme Corp">`, company_name = "Acme Corp"
- Given `<span data-location="London">`, location = "London"
- Given body text "this is a full-time position", role_type = "full-time"

**`tests/adapters/openai.test.js`**:

- `company_name()` always returns "OpenAI"
- `slugToLocation` on `.../san-francisco/` returns "San Francisco"
- `slugToLocation` on `.../remote/` returns "Remote"
- `slugToLocation` on unknown slug returns null → falls back to generic
- Given `<h1>Engineer</h1><p>San Francisco, CA</p>`, location = "San Francisco, CA"

**`tests/content.test.js`** (integration):

- Given an OpenAI-shaped DOM, `extractJobData()` returns company = "OpenAI"
- Given a generic DOM, `extractJobData()` returns same result as before (regression guard)

### No `data-model.md` or `contracts/`

Pure client-side JS change. No new backend entities or API surface. Both skipped.

## Implementation Strategy

1. Write Jest test fixtures — confirm they fail (Red)
2. Rewrite `content.js` with registry framework + generic adapter + OpenAI adapter
3. Run `npm test` in `chrome-extension/` — all tests pass (Green)
4. Run `make check` from project root — no regressions
5. Manual smoke test: OpenAI URL + one existing site
6. Commit
