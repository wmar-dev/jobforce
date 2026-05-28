# Jobforce — Superhero Job Hunt Command Center

A personal job search assistant powered by Claude AI. Five specialized agents — each with a superhero theme — help you find, rank, tailor, and prep for jobs.

| Agent      | Color   | Role                                   |
| ---------- | ------- | -------------------------------------- |
| **Scout**  | Emerald | Crawl and ingest job listings          |
| **Oracle** | Violet  | Rank jobs by fit against your profile  |
| **Forge**  | Amber   | Tailor your resume to a specific job   |
| **Coach**  | Blue    | Generate interview prep questions      |
| **HQ**     | Red     | Dashboard overview of your pipeline    |

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 async + aiosqlite (SQLite WAL)
- **Frontend**: Next.js 14 + Tailwind CSS + SWR
- **AI**: Claude Haiku via Anthropic SDK
- **Chrome Extension**: Manifest V3 — capture jobs while browsing
- **Crawling**: Playwright MCP skill for automated job ingestion

## Prerequisites

- Python 3.12+ with [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+
- LaTeX (optional — for PDF resume export): `brew install --cask mactex`
- Chrome (for the extension)

## Setup

```bash
# 1. Install dependencies
make install

# 2. Configure
cp config.example.yaml config.yaml
# Edit config.yaml: add your target roles, companies, and profile

# 3. Initialize and seed the database
cd backend && uv run python -m jobforce.db.init
cd backend && uv run python -m jobforce.db.seed

# 4. Start the app (backend + frontend)
make dev
```

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API docs**: <http://localhost:8000/docs>

## Chrome Extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `chrome-extension/` folder
4. Browse to any job listing and click the Jobforce shield icon to save it

## Claude Code Skills

These skills work inside Claude Code (`claude` CLI):

```bash
/oracle-rank          # Rank all saved jobs against your profile
/forge-tailor <id>    # Tailor resume for job #<id> and download PDF
/coach-prep <id>      # Generate interview prep pack for job #<id>
```

## Quality Gates

```bash
make check   # ruff lint + mypy + pytest (backend) + ESLint + Jest (frontend)
```

All gates must pass before committing.

## Configuration

`config.yaml` (gitignored — copy from `config.example.yaml`):

```yaml
database:
  path: "backend/data/jobforce.db"

search:
  queries:
    - query: "Senior Python Engineer"
      location: "Remote, US"
  target_companies:
    - name: "Anthropic"
      domain: "anthropic.com"

user:
  full_name: "Your Name"
  headline: "Senior Software Engineer"
  skills: ["Python", "FastAPI", "React"]
```

## Project Structure

```text
jobforce/
├── backend/                  # FastAPI app
│   ├── jobforce/
│   │   ├── routers/          # scout, oracle, forge, coach, dashboard, …
│   │   ├── services/         # business logic + Claude API calls
│   │   ├── db/               # models, engine, migrations, seed
│   │   └── templates/        # Jinja2 LaTeX resume template
│   └── tests/                # contract + integration + unit
├── frontend/                 # Next.js app
│   └── src/
│       ├── app/              # page routes (HQ, oracle, forge, coach, …)
│       ├── components/       # per-agent UI components
│       └── hooks/            # SWR data hooks
├── chrome-extension/         # MV3 extension
├── config.example.yaml       # config template
└── Makefile                  # dev, check, seed, install
```
