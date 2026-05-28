# Research: Scout Crawl Deterministic Parser

## Decision 1: HTML parsing library

**Decision**: Use Python's stdlib `html.parser` via `html.parser.HTMLParser`, or more practically, `xml.etree.ElementTree` for simple CSS-selector emulation. However, since the Chrome extension uses CSS selectors and BeautifulSoup has the closest 1:1 mapping, we should add `beautifulsoup4` + `lxml` as a backend dependency.

**Rationale**: BeautifulSoup's `select()` method accepts CSS selectors directly — `doc.select_one("main h2")` mirrors JS's `doc.querySelector("main h2")` exactly. This makes porting adapters from the Chrome extension's JS a mechanical translation, reduces the chance of selector drift, and is the de facto standard for Python HTML parsing. The `lxml` backend is faster and more lenient than the stdlib `html.parser` for malformed HTML.

**Alternatives considered**:
- `html.parser` (stdlib) — no CSS selector support; would need manual tree walking for each adapter field.
- `lxml` alone — has CSS selectors via `cssselect` but requires extra package and less ergonomic API than BeautifulSoup.
- Regex over raw HTML — brittle, hard to maintain, produces inconsistent results.

---

## Decision 2: Where does the parser live?

**Decision**: A new module `jobforce/services/parse.py` in the backend, callable from a thin CLI entry point `jobforce/cli/parse_job.py` that the scout-crawl skill invokes via `uv run python -m jobforce.cli.parse_job`.

**Rationale**: The parsing logic belongs in the backend alongside the ingest service it feeds. Placing it in `services/parse.py` means it can also be called directly from integration tests without subprocess indirection. The CLI wrapper lets the skill invoke it with `--url` and `--html-file` arguments and receive JSON on stdout.

**Alternatives considered**:
- Standalone script outside the package — would not benefit from the existing virtualenv and `uv` toolchain.
- New top-level `tools/` directory — adds directory complexity without benefit since the backend venv is already present.

---

## Decision 3: How does the skill invoke the parser?

**Decision**: The skill saves the Playwright-captured HTML to a temp file within the allowed Playwright MCP root, then invokes `cd backend && uv run python -m jobforce.cli.parse_job --url <URL> --html-file <path>`, reads stdout JSON, and uses those fields in the ingest POST.

**Rationale**: Passing HTML via a file avoids shell argument length limits (job pages can be 200–400 KB). The module entrypoint approach (`-m`) works reliably with `uv run` and is consistent with how the seed script is invoked (`uv run python -m jobforce.db.seed`).

**Alternatives considered**:
- Passing HTML via stdin — cleaner but harder to debug; file approach gives a reproducible artifact.
- Building a new `/api/parse` endpoint — adds HTTP round-trip and a new API surface just for an internal skill need.

---

## Decision 4: Adapter registry design in Python

**Decision**: Mirror the Chrome extension's pattern exactly: a `GENERIC_ADAPTER` dict of `{field: Callable[[BeautifulSoup], str | None]}`, a `SITE_ADAPTERS` dict of `{hostname: adapter_dict}`, `run_adapter()`, `merge()`, and `slug_to_location()` helpers — all in `services/parse.py`.

**Rationale**: Direct structural parity means adding a new adapter only requires translating JS selector syntax to Python BeautifulSoup syntax. The `merge()` logic (specific overrides generic when non-null/non-empty) is trivially expressible in Python and keeps the two implementations auditable against each other.

**Alternatives considered**:
- Class-based adapters — more overhead, no benefit for this level of complexity.
- Shared config file (YAML/JSON) for selectors — loses the ability to have field-level Python logic (e.g., `slug_to_location`, `role_type` regex).

---

## Dependency Addition Required

`beautifulsoup4` and `lxml` must be added to `backend/pyproject.toml` under `[project].dependencies`. Neither introduces any conflict with existing dependencies.
