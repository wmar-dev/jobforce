# Data Model: Company Careers Search Skill

## Changed Entity: CompanyConfig (config model)

**Location**: `backend/jobforce/config.py`

| Field         | Type  | Default | Description                                             |
| ------------- | ----- | ------- | ------------------------------------------------------- |
| `name`        | `str` | —       | Company display name (existing)                         |
| `domain`      | `str` | `""`    | Company domain for careers URL discovery (existing)     |
| `careers_url` | `str` | `""`    | Seed hint; written to DB on seed. Empty = auto-discover |

## Changed Entity: Company (DB model)

**Location**: `backend/jobforce/db/models.py`

| Column        | Type          | Nullable | Description                                                  |
| ------------- | ------------- | -------- | ------------------------------------------------------------ |
| `id`          | Integer PK    | No       | (existing)                                                   |
| `name`        | Text unique   | No       | (existing)                                                   |
| `domain`      | Text          | Yes      | (existing)                                                   |
| `notes`       | Text          | Yes      | (existing)                                                   |
| `careers_url` | Text          | Yes      | Careers page URL; seeded from config or written back by skill after auto-discovery        |
| `created_at`  | Text          | No       | (existing)                                                   |
| `updated_at`  | Text          | No       | (existing)                                                   |

**Migration**: `ALTER TABLE companies ADD COLUMN careers_url TEXT` (SQLite; no default needed since nullable).

### Write-back flow

When the skill auto-discovers a careers URL from a company's `domain`, it writes it back via `PATCH /api/companies/{id}` so future runs skip re-probing. The seed also populates `careers_url` from `config.yaml` if set.

## New Endpoint: PATCH /api/companies/{id}

**Location**: `backend/jobforce/routers/companies.py`

```text
PATCH /api/companies/{company_id}
Body: { "careers_url": "https://..." }
Response 200: { "id": ..., "name": ..., "domain": ..., "careers_url": ... }
Response 404: company not found
```

Partial update — only `careers_url` is patchable for now (the skill is the only caller). Future fields can be added to the patch body as needed.

## New Endpoint: GET /api/companies

**Location**: `backend/jobforce/routers/companies.py`

```text
GET /api/companies
Response 200: [{ "id": ..., "name": ..., "domain": ..., "careers_url": ... }, ...]
```

The skill needs to look up company IDs by name to call the PATCH endpoint. This list endpoint enables that without a separate lookup.

## Skill Runtime Model (in-memory only, not persisted)

```
CrawlResult:
  company_name: str
  careers_url_used: str
  jobs_ingested: int
  jobs_skipped: int        # duplicates (409)
  errors: list[str]
```
