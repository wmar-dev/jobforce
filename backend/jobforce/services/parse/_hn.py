# ---------------------------------------------------------------------------
# Hacker News site adapter — news.ycombinator.com/item?id=<comment-id>
# Single-comment page layout: table.fatitem > tr.athing > td.default >
#   div.comment > div.commtext
# Dead/flagged comments have class "cdd" or "cdf" on the commtext element.
#
# This adapter bypasses the SITE_ADAPTERS framework entirely — parse_html
# dispatches straight to _parse_hn() for this hostname.
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup, Tag

from ._common import _to_markdown

logger = logging.getLogger(__name__)


def _hn_extract_commtext(soup: BeautifulSoup) -> Tag | None:
    """Return the .commtext Tag from a single-comment fatitem page, or None."""
    el = soup.select_one(".fatitem .commtext")
    if el is None:
        return None
    classes: list[str] = el.get("class") or []  # type: ignore[assignment]
    if "cdd" in classes or "cdf" in classes:
        return None
    return el


def _hn_first_line(commtext: Tag) -> str:
    """Return the first non-empty text line from a commtext element."""
    raw = commtext.get_text(separator="\n")
    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _hn_role_type_from_tokens(tokens: list[str]) -> str | None:
    """Scan pipe tokens for employment-type keywords; return canonical value."""
    for token in tokens:
        t = token.lower().strip()
        if "full-time" in t or "full time" in t:
            return "full-time"
        if "part-time" in t or "part time" in t:
            return "part-time"
        if "contract" in t:
            return "contract"
        if "intern" in t:
            return "internship"
    return None


def _hn_parse_pipe(first_line: str) -> dict[str, str | None]:
    """Extract structured fields from a pipe-delimited HN first line."""
    tokens = [t.strip() for t in first_line.split("|")]
    company = tokens[0] if tokens else None
    title = tokens[1] if len(tokens) > 1 else None
    location = tokens[2] if len(tokens) > 2 else None
    role_type = _hn_role_type_from_tokens(tokens)
    return {
        "company_name": company or None,
        "title": title or None,
        "location": location or None,
        "role_type": role_type,
    }


def _parse_hn(html: str, url: str) -> dict[str, Any]:
    """HN single-comment adapter — deterministic, zero LLM calls."""
    soup = BeautifulSoup(html, "lxml")
    commtext = _hn_extract_commtext(soup)
    if commtext is None:
        logger.warning("hn adapter: commtext not found for %s", url)
        return {"source_url": url}

    first_line = _hn_first_line(commtext)
    description = _to_markdown(commtext)

    if "|" in first_line:
        fields = _hn_parse_pipe(first_line)
    else:
        # Prose format: use first word-token as company, leave title/location null
        first_token = first_line.split()[0].rstrip(".,;:") if first_line.split() else None
        fields = {
            "company_name": first_token,
            "title": None,
            "location": None,
            "role_type": _hn_role_type_from_tokens([first_line]),
        }

    return {
        "source_url": url,
        "company_name": fields.get("company_name"),
        "title": fields.get("title"),
        "location": fields.get("location"),
        "role_type": fields.get("role_type"),
        "description": description,
    }
