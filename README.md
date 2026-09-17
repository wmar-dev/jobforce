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
- **Frontend**: Next.js 15 + Tailwind CSS + SWR
- **AI**: Claude Haiku via Anthropic SDK
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

### `target_companies.yaml`

A tracked, curated list of ~1,000 companies with `domain`/`careers_url` filled
in where verified. It isn't read by any code — it's a shared starting point
for `search.target_companies` above. Copy the entries you want into your own
`config.yaml`.

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
├── config.example.yaml                        # config template
├── config/resume.example.json                 # resume template
├── config/tailoring-instructions.example.md  # tailoring constraints template
└── Makefile                                   # dev, check, seed, install
```
