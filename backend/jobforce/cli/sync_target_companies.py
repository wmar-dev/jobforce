"""CLI: copy companies from config.yaml into the shared target_companies.yaml list.

Usage:
    uv run python -m jobforce.cli.sync_target_companies           # dry run: print what would be added
    uv run python -m jobforce.cli.sync_target_companies --write   # update target_companies.yaml
    uv run python -m jobforce.cli.sync_target_companies --source ../candidate-labs.yaml --write
        # read companies from a standalone YAML list (name/domain/careers_url) instead of
        # config.yaml; the list may be top-level or nested under one key, extra fields ignored

Adds every search.target_companies entry (or --source entry) whose name (normalized: lowercase,
alphanumerics only) is not already in target_companies.yaml. Existing entries,
including their inline comments, are kept verbatim; new entries are inserted
in alphabetical order. Hacker News threads and job-board aggregators are
skipped since they are not company careers pages, as are entries whose
careers_url is already listed (the same company under another name).
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

import yaml

from jobforce.cli.config_lookup import _load_company_file
from jobforce.config import _find_config, load_config

# Careers URLs that point at multi-company sources, not a single company.
_AGGREGATOR_HOSTS = ("news.ycombinator.com", "jobs.sequoiacap.com")

_ENTRY_START = re.compile(r"(?m)^(?=    - name:)")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _clean_domain(domain: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", domain.strip()).rstrip("/")


def _render(company: dict[str, str]) -> str:
    def q(s: str) -> str:
        return json.dumps(s, ensure_ascii=False)

    return (
        f"    - name: {q(company['name'])}\n"
        f"      domain: {q(_clean_domain(company['domain']))}\n"
        f"      careers_url: {q(company['careers_url'])}\n"
    )


def _url_key(url: str) -> str:
    url = re.sub(r"^https?://(www\.)?", "", url.strip().lower()).rstrip("/")
    return url.replace("job-boards.greenhouse.io", "boards.greenhouse.io")


def merge(
    target_text: str, companies: list[dict[str, str]], *, skip_name_only: bool = False
) -> tuple[str, list[str], dict[str, str]]:
    """Return (new_text, added_names, {skipped_name: reason}) for merging into target_text."""
    head, *blocks = _ENTRY_START.split(target_text)
    entries: list[tuple[str, str]] = []
    # careers_url -> name, to catch the same company listed under another name
    urls: dict[str, str] = {}
    for block in blocks:
        parsed: Any = yaml.safe_load(block)
        name = parsed[0]["name"]
        entries.append((name, block if block.endswith("\n") else block + "\n"))
        if parsed[0].get("careers_url"):
            urls.setdefault(_url_key(parsed[0]["careers_url"]), name)
    existing = {_norm(name) for name, _ in entries}

    new: dict[str, dict[str, str]] = {}
    skipped: dict[str, str] = {}
    for c in companies:
        if any(host in c["careers_url"] for host in _AGGREGATOR_HOSTS):
            skipped[c["name"]] = "aggregator"
            continue
        if skip_name_only and not (c["careers_url"] or c["domain"]):
            skipped[c["name"]] = "no careers_url or domain"
            continue
        key = _norm(c["name"])
        if key in existing:
            continue
        # On duplicate entries, prefer the first one that has a careers_url
        if key in new and new[key]["careers_url"]:
            continue
        url = _url_key(c["careers_url"]) if c["careers_url"] else ""
        if url in urls:
            skipped[c["name"]] = f"same careers_url as {urls[url]}"
            continue
        new[key] = c
        if url:
            urls[url] = c["name"]

    # A name skipped once may still have been added from a later, more complete entry
    skipped = {name: why for name, why in skipped.items() if _norm(name) not in new}
    entries += [(c["name"], _render(c)) for c in new.values()]
    entries.sort(key=lambda e: e[0].lower())
    return head + "".join(block for _, block in entries), [c["name"] for c in new.values()], skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy companies from config.yaml into target_companies.yaml"
    )
    parser.add_argument("--write", action="store_true", help="update the file (default: dry run)")
    parser.add_argument("--target", default="target_companies.yaml", help="shared list to update")
    parser.add_argument("--source", help="YAML company list to read instead of config.yaml")
    parser.add_argument(
        "--skip-name-only",
        action="store_true",
        help="skip entries that have neither a careers_url nor a domain",
    )
    args = parser.parse_args()

    companies = (
        _load_company_file(args.source)
        if args.source
        else [
            {"name": c.name, "domain": c.domain or "", "careers_url": c.careers_url or ""}
            for c in load_config().search.target_companies
        ]
    )
    target = _find_config(args.target)
    new_text, added, skipped = merge(
        target.read_text(encoding="utf-8"), companies, skip_name_only=args.skip_name_only
    )
    if args.write and added:
        target.write_text(new_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "source": args.source or "config.yaml",
                "target": str(target),
                "written": bool(args.write and added),
                "added": added,
                "skipped": skipped,
            }
        )
    )


if __name__ == "__main__":
    main()
