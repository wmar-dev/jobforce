"""CLI: copy companies from config.yaml into the shared target_companies.yaml list.

Usage:
    uv run python -m jobforce.cli.sync_target_companies           # dry run: print what would be added
    uv run python -m jobforce.cli.sync_target_companies --write   # update target_companies.yaml

Adds every search.target_companies entry whose name (normalized: lowercase,
alphanumerics only) is not already in target_companies.yaml. Existing entries,
including their inline comments, are kept verbatim; new entries are inserted
in alphabetical order. Hacker News threads and job-board aggregators are
skipped since they are not company careers pages.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

import yaml

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


def merge(target_text: str, companies: list[dict[str, str]]) -> tuple[str, list[str], list[str]]:
    """Return (new_text, added_names, skipped_names) for merging companies into target_text."""
    head, *blocks = _ENTRY_START.split(target_text)
    entries: list[tuple[str, str]] = []
    for block in blocks:
        parsed: Any = yaml.safe_load(block)
        entries.append((parsed[0]["name"], block if block.endswith("\n") else block + "\n"))
    existing = {_norm(name) for name, _ in entries}

    new: dict[str, dict[str, str]] = {}
    skipped: list[str] = []
    for c in companies:
        if any(host in c["careers_url"] for host in _AGGREGATOR_HOSTS):
            skipped.append(c["name"])
            continue
        key = _norm(c["name"])
        if key in existing:
            continue
        # On duplicate config entries, prefer the first one that has a careers_url
        if key in new and new[key]["careers_url"]:
            continue
        new[key] = c

    entries += [(c["name"], _render(c)) for c in new.values()]
    entries.sort(key=lambda e: e[0].lower())
    return head + "".join(block for _, block in entries), [c["name"] for c in new.values()], skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy companies from config.yaml into target_companies.yaml"
    )
    parser.add_argument("--write", action="store_true", help="update the file (default: dry run)")
    parser.add_argument("--target", default="target_companies.yaml", help="shared list to update")
    args = parser.parse_args()

    companies = [
        {"name": c.name, "domain": c.domain or "", "careers_url": c.careers_url or ""}
        for c in load_config().search.target_companies
    ]
    target = _find_config(args.target)
    new_text, added, skipped = merge(target.read_text(encoding="utf-8"), companies)
    if args.write and added:
        target.write_text(new_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "target": str(target),
                "written": bool(args.write and added),
                "added": added,
                "skipped_aggregators": skipped,
            }
        )
    )


if __name__ == "__main__":
    main()
