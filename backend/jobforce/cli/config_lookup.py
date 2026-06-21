"""CLI tool: look up scout config (companies, target_roles, target_locations) from config.yaml.

Usage:
    uv run python -m jobforce.cli.config_lookup              # all companies
    uv run python -m jobforce.cli.config_lookup "Abridge"    # single company by name (case-insensitive)
"""

from __future__ import annotations

import json
import sys

from jobforce.config import load_config


def main() -> None:
    name_filter = sys.argv[1].strip().lower() if len(sys.argv) > 1 else None

    cfg = load_config()
    search = cfg.search
    prefs = cfg.user.preferences if cfg.user and cfg.user.preferences else {}
    get_pref = lambda k: prefs.get(k, []) if isinstance(prefs, dict) else getattr(prefs, k, [])

    all_companies = [
        {"name": c.name, "domain": c.domain, "careers_url": c.careers_url}
        for c in search.target_companies
    ]

    if name_filter is not None:
        companies = [c for c in all_companies if c["name"].lower() == name_filter]
        out = {
            "companies": companies,
            "target_roles": get_pref("target_roles"),
            "target_locations": getattr(search, "target_locations", None) or [],
            "total_companies": len(all_companies),
        }
    else:
        out = {
            "companies": all_companies,
            "target_roles": get_pref("target_roles"),
            "target_locations": getattr(search, "target_locations", None) or [],
        }

    print(json.dumps(out))


if __name__ == "__main__":
    main()
