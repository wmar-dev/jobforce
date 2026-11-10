"""Write the API's OpenAPI document to ``backend/openapi.yaml``.

The document is generated from the FastAPI route declarations so the checked-in
contract can never be hand-edited out of sync with the code. ``--check`` compares
instead of writing; the drift test in ``tests/contract`` enforces it in ``make check``.

Usage::

    python -m jobforce.cli.export_openapi          # write
    python -m jobforce.cli.export_openapi --check  # exit 1 if stale
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "openapi.yaml"
STALE_MESSAGE = "openapi.yaml is out of date — run: cd backend && make openapi"


def render_openapi_yaml() -> str:
    """Render the OpenAPI document as deterministic YAML (no config or DB access)."""
    from jobforce.main import create_app

    doc = create_app().openapi()
    # sort_keys=False keeps FastAPI's insertion order, which mirrors the code layout.
    text: str = yaml.safe_dump(
        doc, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False
    )
    return text.rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--check", action="store_true", help="fail if the file is stale")
    args = parser.parse_args(argv)

    rendered = render_openapi_yaml()
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else None
        if current != rendered:
            print(STALE_MESSAGE, file=sys.stderr)
            return 1
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    logger.info("Wrote %s", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
