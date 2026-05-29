# Data Model: Company Careers Search Skill

## Changed Entity: CompanyConfig

**Location**: `backend/jobforce/config.py`

| Field        | Type  | Default | Description                                              |
| ------------ | ----- | ------- | -------------------------------------------------------- |
| `name`       | `str` | —       | Company display name (existing)                          |
| `domain`     | `str` | `""`    | Company domain for careers URL discovery (existing)      |
| `careers_url`| `str` | `""`    | Direct careers page URL; bypasses auto-discovery if set  |

**Validation**: No new validators needed. Empty string = auto-discover from `domain`.

## No DB Schema Changes

`CompanyConfig` is a config-only Pydantic model. The `companies` DB table (`name`, `domain`) is seeded from config but does not store `careers_url` — it's a runtime hint for the skill only.

## Skill Runtime Model (in-memory only)

```
CrawlResult (not persisted):
  company_name: str
  careers_url_used: str
  jobs_ingested: int
  jobs_skipped: int        # duplicates (409)
  errors: list[str]
```

Used only for the skill's final summary report.
