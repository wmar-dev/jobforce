"""CLI tool: look up scout config (companies, target_roles, target_locations) from config.yaml.

Usage:
    uv run python -m jobforce.cli.config_lookup              # all companies
    uv run python -m jobforce.cli.config_lookup "Abridge"    # single company by name (case-insensitive)
    uv run python -m jobforce.cli.config_lookup --file ../candidate-labs.yaml [name]
        # companies from a standalone YAML list (name/domain/careers_url) instead of config.yaml
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

from jobforce.config import load_config


def _get_pref(prefs: Any, key: str) -> Any:
    return prefs.get(key, []) if isinstance(prefs, dict) else getattr(prefs, key, [])


def _load_company_file(path: str) -> list[dict[str, Any]]:
    raw = yaml.safe_load(Path(path).read_text()) or []
    return [
        {
            "name": c["name"],
            "domain": c.get("domain") or "",
            "careers_url": c.get("careers_url") or "",
        }
        for c in raw
    ]


def main() -> None:
    args = sys.argv[1:]
    company_file: str | None = None
    if "--file" in args:
        i = args.index("--file")
        company_file = args[i + 1]
        del args[i : i + 2]
    name_filter = args[0].strip().lower() if args else None

    cfg = load_config()
    search = cfg.search
    prefs = cfg.user.preferences if cfg.user and cfg.user.preferences else {}

    all_companies = (
        _load_company_file(company_file)
        if company_file
        else [
            {"name": c.name, "domain": c.domain, "careers_url": c.careers_url}
            for c in search.target_companies
        ]
    )

    if name_filter is not None:
        companies = [c for c in all_companies if c["name"].lower() == name_filter]
        out = {
            "companies": companies,
            "target_roles": _get_pref(prefs, "target_roles"),
            "target_locations": getattr(search, "target_locations", None) or [],
            "total_companies": len(all_companies),
        }
    else:
        out = {
            "companies": all_companies,
            "target_roles": _get_pref(prefs, "target_roles"),
            "target_locations": getattr(search, "target_locations", None) or [],
        }

    print(json.dumps(out))


if __name__ == "__main__":
    main()
