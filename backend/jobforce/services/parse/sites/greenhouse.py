# ---------------------------------------------------------------------------
# Greenhouse site adapter — boards.greenhouse.io / job-boards.greenhouse.io
# (plus the EU-region job-boards.eu.greenhouse.io tenants, e.g. Groww)
# URL: boards.greenhouse.io/<company>/jobs/<id>
#
# Some boards (e.g. Patronus AI) use an application-only layout: the page
# renders just the apply form — no h1/.job__title, .job__location or
# .job__description — and the job itself only exists in the inline Remix
# context's `jobPost` payload (title, job_post_location, content,
# company_name). Every field below tries the DOM first and falls back to that
# payload. scout_fetch also synthesizes a `jobPost` payload from the public
# boards API for boards whose job URLs redirect to the company's own careers
# page (e.g. Unconventional AI -> unconv.ai/careers/?gh_jid=<id>).
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown, normalize_posted_at

HOSTNAMES = ["boards.greenhouse.io", "job-boards.greenhouse.io", "job-boards.eu.greenhouse.io"]


_JOB_POST_KEY_RE = re.compile(r'"jobPost"\s*:\s*')
_LEGAL_SUFFIX_RE = re.compile(r"[\s,]+(inc|incorporated|llc|ltd|corp|corporation|co)\.?$", re.I)


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip() or None


def _job_post(doc: BeautifulSoup) -> dict[str, Any]:
    """The inline Remix `jobPost` payload ({} if absent)."""
    decoder = json.JSONDecoder()
    for script in doc.find_all("script"):
        text = script.string or ""
        match = _JOB_POST_KEY_RE.search(text)
        if match is None:
            continue
        try:
            payload, _ = decoder.raw_decode(text, match.end())
        except ValueError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _squash(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _greenhouse_title(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is not None and (t := _clean(_text(h1))):
        return t
    return _clean(_job_post(doc).get("title"))


def _greenhouse_company(doc: BeautifulSoup, url: str) -> str | None:
    slug_name = _greenhouse_slug_company(url)
    # Prefer the payload's real company name (e.g. "Patronus AI, Inc." over
    # slug "patronusaiinc"), but only when it is just a reformatting of the
    # slug — otherwise existing company records keyed on the slug name would
    # stop matching.
    payload_name = _clean(_job_post(doc).get("company_name"))
    if slug_name and payload_name:
        stripped = _LEGAL_SUFFIX_RE.sub("", payload_name) or payload_name
        if _squash(slug_name) in (_squash(payload_name), _squash(stripped)):
            return stripped
    return slug_name


def _greenhouse_slug_company(url: str) -> str | None:
    # boards.greenhouse.io/<company>/jobs/<id> — extract from path
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if parts[0] == "embed":
        # boards.greenhouse.io/embed/job_app?for=<board>&token=<id>
        board = (parse_qs(parsed.query).get("for") or [""])[0].rstrip("0123456789")
        return " ".join(w.capitalize() for w in board.replace("-", " ").split()) or None
    if len(parts) >= 1 and parts[0] not in ("jobs",):
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _greenhouse_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job__location")
    return _text(el) or _clean(_job_post(doc).get("job_post_location"))


def _greenhouse_description(doc: BeautifulSoup, url: str) -> str | None:
    # Normal layout: let the generic `[class*="description"]` selector handle
    # .job__description. Application-only layout: that selector would match
    # an apply-form `.question-description` instead, so build the description
    # from the payload's introduction/content/conclusion HTML.
    if doc.select_one(".job__description") is not None:
        return None
    job_post = _job_post(doc)
    parts = [job_post.get(k) for k in ("introduction", "content", "conclusion")]
    body = "\n".join(p for p in parts if isinstance(p, str) and p.strip())
    if not body:
        return None
    return _to_markdown(BeautifulSoup(f"<div>{body}</div>", "lxml").div)


_PUBLISHED_AT_RE = re.compile(r'"published_at"\s*:\s*"([^"]+)"')


def _greenhouse_posted_at(doc: BeautifulSoup, url: str) -> str | None:
    # job-boards.greenhouse.io is a Remix app: the job payload (including
    # `published_at`, the original posting date) is embedded in an inline
    # script, but there is no visible date or JSON-LD on the page.
    for script in doc.find_all("script"):
        match = _PUBLISHED_AT_RE.search(script.string or "")
        if match and (normalized := normalize_posted_at(match.group(1))):
            return normalized
    return None


ADAPTER: dict[str, Any] = {
    "title": _greenhouse_title,
    "company_name": _greenhouse_company,
    "location": _greenhouse_location,
    "description": _greenhouse_description,
    "posted_at": _greenhouse_posted_at,
}
