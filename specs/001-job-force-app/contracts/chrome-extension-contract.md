# Contract: Chrome Extension ↔ FastAPI

## Extension → FastAPI

**Endpoint**: `POST http://localhost:8000/api/ingest`

**Trigger**: User clicks the Jobforce extension button on a job listing page.

**Content script** extracts from DOM:
- `document.title` → job title (fallback)
- `document.location.href` → `source_url`
- `document.documentElement.outerHTML` → `html`
- Structured fields parsed by content script if detectable
  (title, company, location, description)

**Service worker** POSTs:
```json
{
  "source_url": "string (required)",
  "html": "string (required, raw page HTML)",
  "title": "string (optional, parsed from page)",
  "company_name": "string (optional)",
  "location": "string (optional)",
  "description": "string (optional)"
}
```

**Success response (201 or 409)**:
Extension shows badge notification: ✅ "Saved" or "Already saved".

**Failure (5xx or network error)**:
Extension shows badge: ❌ "Server not running — start Jobforce backend".

## Extension Permissions (manifest.json)

```json
{
  "permissions": ["activeTab", "storage", "scripting"],
  "host_permissions": ["http://localhost:8000/*"],
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "run_at": "document_idle"
  }]
}
```

## State stored in chrome.storage.local

```json
{
  "backend_url": "http://localhost:8000",
  "last_ingested_url": "https://...",
  "last_ingested_at": "2026-05-27T10:00:00Z"
}
```
