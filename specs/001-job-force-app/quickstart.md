# Quickstart: Jobforce — Superhero Job Hunt Command Center

## Prerequisites

- Python 3.14+ with `uv` or `pip`
- Node.js 20+ with `npm`
- LaTeX distribution: `texlive-full` (macOS: `brew install --cask mactex`)
- Claude Code CLI (`npm install -g @anthropic-ai/claude-code`)
- Chrome browser (for extension)

---

## 1. Clone and Install

```bash
git clone <repo-url> && cd jobforce

# Backend
cd backend && pip install -e ".[dev]"

# Frontend
cd ../frontend && npm install

# Register Playwright MCP
claude mcp add playwright npx @playwright/mcp@latest
```

---

## 2. Configure

```bash
cp config.example.yaml config.yaml
# Edit config.yaml: add your target roles, companies, preferences
```

Minimum `config.yaml`:
```yaml
database:
  path: backend/data/jobforce.db

search:
  queries:
    - text: "Senior Python Engineer"
      location: "Remote, US"
  target_companies:
    - name: "Anthropic"
      domain: "anthropic.com"

user:
  full_name: "Your Name"
  skills: ["Python", "FastAPI", "React"]
```

---

## 3. Initialize Database

```bash
cd backend
python -m jobforce.db.init          # creates DB, runs migrations
python -m jobforce.db.seed          # seeds from config.yaml
```

---

## 4. Start the App

```bash
# From repo root — starts both backend and frontend
npm run dev
```

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API docs**: http://localhost:8000/docs

---

## 5. Load the Chrome Extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select `chrome-extension/` folder
4. The Jobforce shield icon appears in your toolbar

---

## 6. Capture Your First Job

**Option A — Chrome extension** (manual browse):
1. Navigate to a job listing on any job board
2. Click the Jobforce shield icon
3. Confirm "✅ Saved" badge

**Option B — Playwright MCP** (automated):
```bash
# In Claude Code
/speckit-scout-crawl https://jobs.example.com/posting/123
```

---

## 7. Run the Hero Agents

```bash
# Oracle: rank all saved jobs
/speckit-oracle-rank

# Forge: tailor resume for job #42 and download PDF
/speckit-forge-tailor 42

# Coach: get interview prep for job #42
/speckit-coach-prep 42
```

---

## 8. Quality Gates

```bash
cd backend && make check    # ruff lint + mypy + pytest
cd frontend && npm run lint && npm test
```

All gates must pass before committing.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Extension shows ❌ "Server not running" | Run `npm run dev` first |
| `latexmk: command not found` | Install MacTeX: `brew install --cask mactex` |
| `aiosqlite` lock errors | Ensure only one backend process is running |
| Playwright MCP auth required | Log in manually in the visible browser window when prompted |
