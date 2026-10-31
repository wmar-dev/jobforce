# Jobforce — Superhero Job Hunt Command Center

A personal job search assistant powered by Claude AI. Five specialized agents — each with a superhero theme — help you find, rank, tailor, and prep for jobs.

| Agent      | Color   | Role                                   |
| ---------- | ------- | -------------------------------------- |
| **Scout**  | Emerald | Crawl and ingest job listings          |
| **Oracle** | Violet  | Rank jobs by fit against your profile  |
| **Forge**  | Amber   | Tailor your resume to a specific job   |
| **Coach**  | Blue    | Generate interview prep questions      |
| **HQ**     | Red     | Dashboard overview of your pipeline    |

## Inspiration

I wanted to practice spec-driven design and ran out of tokens when I tried to use [career-ops](https://github.com/santifer/career-ops/issues/98).

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 async + aiosqlite (SQLite WAL)
- **Frontend**: Next.js 16 + React 19 + Tailwind CSS v4 + SWR
- **AI**: Claude Code skills reasoning in-context (no API key required) — the backend has no Anthropic SDK dependency
- **Chrome Extension**: Manifest V3 — capture jobs while browsing
- **Crawling**: Playwright MCP skill for automated job ingestion

## Prerequisites

Developed and tested on macOS; should also run on Linux without changes (both are POSIX).

- Python 3.12+ with [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+
- LaTeX (optional — for PDF resume export, requires `latexmk`):
  - macOS full install: `brew install --cask mactex` (~5GB, includes `latexmk`)
  - macOS lightweight: `brew install --cask basictex`, then `sudo tlmgr update --self && sudo tlmgr install latexmk geometry hyperref parskip`
  - Linux (Debian/Ubuntu): `sudo apt install texlive-latex-extra latexmk`
  - Linux (Fedora): `sudo dnf install texlive-latexmk texlive-collection-latexextra`
- Chrome (for the extension)

**Windows**: use [WSL2](https://learn.microsoft.com/windows/wsl/install) (Ubuntu). The Makefiles, `uv` venv paths, and shell commands below all assume a POSIX environment — running natively in PowerShell/cmd is unsupported. Inside WSL2, follow the Linux instructions above and below as-is.

## Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/wmar-dev/jobforce.git
cd jobforce

# 2. Install dependencies
make install

# 3. Configure
cp config.example.yaml config.yaml
# Edit config.yaml: add your target roles, companies, and profile

cp config/resume.example.json config/resume.json
# Edit config/resume.json: add your work history, skills, and education

cp config/tailoring-instructions.example.md config/tailoring-instructions.md
# Edit config/tailoring-instructions.md: add constraints to prevent false
# information in AI-tailored resume bullets

cp config/scouting-notes.example.md config/scouting-notes.md
# Optional: edit config/scouting-notes.md with freeform guidance on which
# jobs to capture (Avoid/Prefer) and how Oracle should score fit
```

All four files are gitignored so your personal details never get committed. See [Configuration](#configuration) below for what belongs in each one.

```bash
# 4. Initialize and seed the database
cd backend && uv run python -m jobforce.db.init
cd backend && uv run python -m jobforce.db.seed

# 5. Start the app (backend + frontend)
make dev
```

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API docs**: <http://localhost:8000/docs>

## Configuration

Four files under this section are gitignored and personal to you — each is copied from a checked-in `*.example.*` template during [Setup](#setup). Nothing you write into them is ever committed.

### `config.yaml`

Copy from `config.example.yaml`. Drives search queries, the company seed list, and your profile — startup fails if required fields are missing.

```yaml
database:
  path: "backend/data/jobforce.db"

search:
  queries:                    # [REQUIRED] at least one, used to seed SearchConfig records
    - query: "Senior Python Engineer"
      location: "Remote, US"
      source: "linkedin"
  target_locations:           # optional case-insensitive substring filter for scout-companies
    - "Remote"
  target_companies:           # optional — pre-seeds companies into the DB
    - name: "Anthropic"
      domain: "anthropic.com"
      careers_url: ""         # optional direct ATS URL; auto-discovered if blank

user:
  full_name: "Your Name"      # [REQUIRED for Forge PDF export]
  headline: "Senior Software Engineer"
  skills: ["Python", "FastAPI", "React"]   # [REQUIRED for Oracle ranking]
  preferences:
    target_roles: ["Senior Backend Engineer", "Staff Engineer"]
    locations: ["Remote", "San Francisco, CA"]
    role_types: ["full-time"]
    min_salary: null          # optional
```

### `config/resume.json`

Copy from `config/resume.example.json`. Your base profile — seeded into the `resumes` table (`is_base=1`) on `db.seed`, and the source Oracle scores against and Forge tailors from. Fill in `personal_info`, `summary`, `skills`, `work_history` (with `bullets` per role), `education`, `projects`, `certifications`, and `coursework`. Refresh it later with `/forge-import <resume-file>` instead of hand-editing once your real resume changes.

### `config/tailoring-instructions.md`

Copy from `config/tailoring-instructions.example.md`. Guardrails applied on every `/forge-tailor` run, mainly to stop the AI from fabricating or exaggerating bullets — e.g. "never invent metrics/tools not already in the base resume," "never change titles, companies, or dates." Also has a **Clarifications** section that Forge appends to automatically as it asks you disambiguating questions during tailoring, so it doesn't ask the same thing twice.

### `config/scouting-notes.md`

Copy from `config/scouting-notes.example.md`. Optional — both skills run fine without it. Freeform guidance that `config.yaml`'s structured fields can't express: an **Avoid** section (company types/role patterns to skip during `/scout-companies`, e.g. staffing agencies, in-office-only roles), a **Prefer** section (positive signals for `/oracle-rank` to weight up), and **Scoring notes** (context for Oracle's fit rationale that isn't derivable from the resume alone, e.g. "don't penalize on-call requirements").

### `target_companies.yaml`

Checked-in (not gitignored). A tracked, curated list of ~1,000 companies with `domain`/`careers_url` filled in where verified. It isn't read by any code — it's a shared starting point for `search.target_companies` above. Copy the entries you want into your own `config.yaml`. To go the other way and add companies from your `config.yaml` that aren't in the list yet, run `cd backend && uv run python -m jobforce.cli.sync_target_companies` (dry run) and then add `--write`.

## Chrome Extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select the `chrome-extension/` folder
4. Browse to any job listing and click the Jobforce shield icon to save it

## Usage

Once setup is done and `make dev` is running, this is the day-to-day loop. Skills run inside Claude Code (`claude` CLI) from the project root; the frontend at <http://localhost:3000> shows the results of each step.

1. **Capture jobs** — either click the Jobforce shield icon on a job posting in Chrome (see below), or crawl from Claude Code:

   ```bash
   /scout-crawl <job-url>   # Capture a single job listing from its URL
   /scout-companies         # Crawl all target_companies from config.yaml
   ```

   `/scout-companies` filters on `target_roles`/`target_locations` from `config.yaml`, plus any `## Avoid` guidance in `config/scouting-notes.md` if you've set one up.

2. **Rank captured jobs** against your profile:

   ```bash
   /oracle-rank
   ```

   Writes a `fit_score` and rationale back to each job; open the dashboard to see them ranked. Factors in `## Scoring notes` from `config/scouting-notes.md` if present.

3. **Tailor your resume** for a job you're applying to:

   ```bash
   /forge-tailor <job-id>
   ```

   Shows a diff of the tailored bullets and saves a PDF locally (requires LaTeX — see Prerequisites).

4. **Prep for an interview**:

   ```bash
   /coach-prep <job-id>
   ```

   Generates a tailored question pack, visible under that job's Coach tab in the dashboard.

5. **Track status changes** as you hear back:

   ```bash
   /scout-reject <company or job title>   # Mark an application as rejected
   ```

   Other pipeline moves (saved → shortlisted → applied → …) happen from the dashboard UI, which calls `PATCH /api/jobs/{id}/status` under the hood.

6. **Refresh your base resume** whenever your real resume changes:

   ```bash
   /forge-import <path-to-resume.pdf-or-docx>
   ```

   Parses the PDF or DOCX into `config/resume.json`, merging with your existing profile.

If a site adapter fails to parse a listing or a Chrome extension capture is wrong, `/parse-adapter-update <url>` (backend parser) and `/site-adapter-update <url>` (extension) regenerate the site-specific extractors.

### Using the dashboard

The AI reasoning (ranking, tailoring, prep) happens in Claude Code skills, but the dashboard at <http://localhost:3000> is where you browse, filter, and manage everything those skills produce:

| Page | URL | What it's for |
| --- | --- | --- |
| **HQ** | `/` | Pipeline summary (counts per status) and recent activity feed; quick links to the other agents |
| **Scout** | `/jobs` | Browse captured jobs — filter by status/company/location/role type, sort columns, page through results, bulk-archive low-scoring `saved` jobs |
| Job detail | `/jobs/{id}` | Full description, fit score + rationale, change pipeline status (saved → shortlisted → applied → interviewing → offer/rejected/withdrawn), add recruiter/meeting notes |
| **Oracle** | `/oracle` | Review fit scores and rationale written by `/oracle-rank` (read-only here — re-run the skill to (re)score) |
| **Forge** | `/forge` | Edit your base resume inline, pick a job, and copy the `/forge-tailor <id>` command to run in Claude Code |
| **Coach** | `/coach` | Load and review interview prep sessions generated by `/coach-prep <id>` |
| Company detail | `/companies/{id}` | Company profile and recruiter notes, linked from job detail pages |

Manual status changes and note-taking happen entirely in the dashboard; scoring, tailoring, and prep generation require the matching Claude Code skill since that's where the AI reasoning runs.

## Quality Gates

```bash
make check   # ruff lint + mypy + pytest (backend) + ESLint + Jest (frontend)
```

All gates must pass before committing.

## Project Structure

```text
jobforce/
├── backend/                  # FastAPI app
│   ├── jobforce/
│   │   ├── routers/          # scout, oracle, forge, coach, dashboard, …
│   │   ├── services/         # business logic (incl. services/parse/sites/ site adapters)
│   │   ├── cli/              # one-off scripts (scout_fetch, merge_companies, …)
│   │   ├── db/               # models, engine, migrations, seed
│   │   └── templates/        # Jinja2 LaTeX resume template
│   └── tests/                # contract + integration + unit + fixtures
├── frontend/                 # Next.js app
│   └── src/
│       ├── app/              # page routes (HQ, oracle, forge, coach, …)
│       ├── components/       # per-agent UI components
│       ├── hooks/            # SWR data hooks
│       └── lib/              # API client + shared types
├── chrome-extension/         # MV3 extension
├── config.example.yaml                        # config template
├── config/resume.example.json                 # resume template
├── config/tailoring-instructions.example.md  # tailoring constraints template
├── config/scouting-notes.example.md          # scouting/scoring guidance template
└── Makefile                                   # dev, check, seed, install
```

Maintaining the repo itself (dependency upgrade policy, maintainer-only skills like `/housekeeping`)? See [DEVELOPMENT.md](DEVELOPMENT.md).
