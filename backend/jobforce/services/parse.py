"""Deterministic job page parser — mirrors chrome-extension/content.js adapter architecture."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

logger = logging.getLogger(__name__)

_CITIES = [
    "san-francisco",
    "new-york",
    "london",
    "seattle",
    "remote",
    "boston",
    "chicago",
    "austin",
]


def slug_to_location(pathname: str) -> str | None:
    seg = pathname.rstrip("/").split("/")[-1] or ""
    # Check suffix match first (e.g. "...-san-francisco")
    hit = next((c for c in _CITIES if seg.endswith(c)), None)
    if not hit:
        # Also match city anywhere in slug (e.g. "...-remote-us")
        hit = next((c for c in _CITIES if f"-{c}-" in seg or seg.startswith(f"{c}-")), None)
    if not hit:
        return None
    return " ".join(w.capitalize() for w in hit.split("-"))


def _text(el: Tag | None) -> str | None:
    if el is None:
        return None
    t = (el.get_text(separator=" ") or "").strip()
    return t or None


def _to_markdown(el: Tag | None) -> str | None:
    if el is None:
        return None
    result = md(str(el), heading_style="ATX", bullets="-", strip=["a", "img"]).strip()
    return result or None


# ---------------------------------------------------------------------------
# Generic adapter — equivalent to genericAdapter in content.js
# ---------------------------------------------------------------------------


def _generic_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("h1")
    if el and (t := _text(el)):
        return t
    title_tag = doc.find("title")
    if title_tag:
        raw = (title_tag.get_text() or "").strip()
        return re.sub(r"\s*[-|].*$", "", raw).strip() or None
    return None


def _generic_company(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-company], .company-name, .employer-name")
    if el and (t := _text(el)):
        return t
    meta = doc.find("meta", attrs={"property": "og:site_name"})
    if meta:
        return (meta.get("content") or "").strip() or None  # type: ignore[union-attr]
    return None


def _generic_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-location], .job-location, .location")
    if el and (t := _text(el)):
        return t
    meta = doc.find("meta", attrs={"name": "job:location"})
    if meta:
        return (meta.get("content") or "").strip() or None  # type: ignore[union-attr]
    return None


def _generic_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="description"], [class*="job-desc"], #job-description')
    return _to_markdown(el)


def _generic_role_type(doc: BeautifulSoup, url: str) -> str | None:
    body = doc.body
    t = (body.get_text() if body else "").lower()
    if "full-time" in t or "full time" in t:
        return "full-time"
    if "part-time" in t or "part time" in t:
        return "part-time"
    # Use word boundary to avoid matching "contractor" / "government contractor"
    if re.search(r"\bcontract\b", t):
        return "contract"
    if re.search(r"\bintern(ship)?\b", t):
        return "internship"
    return None


GENERIC_ADAPTER: dict[str, Any] = {
    "title": _generic_title,
    "company_name": _generic_company,
    "location": _generic_location,
    "description": _generic_description,
    "role_type": _generic_role_type,
}

# ---------------------------------------------------------------------------
# OpenAI site adapter — equivalent to openaiAdapter in content.js
# ---------------------------------------------------------------------------


_LOCATION_KEYWORDS = re.compile(
    r"\b(san francisco|new york|seattle|london|boston|chicago|austin|remote)\b",
    re.IGNORECASE,
)


def _openai_location(doc: BeautifulSoup, url: str) -> str | None:
    # First h2 in main is the job title; its next sibling p is the dept/location line
    # e.g. "Robotics - San Francisco" or "Applied AI Engineering - San Francisco and Seattle"
    # Guard: some pages put a team description <p> before the location — skip those.
    # Current hero markup wraps the subhead <p> in a <div> after the h2 rather than
    # making it a direct sibling, so check the explicit data attribute first —
    # it survives that nesting change and multi-location "X, Y, and Z" text alike.
    subhead = doc.select_one('[data-article-hero-copy-region="subhead"]')
    if subhead and (t := _text(subhead)):
        return t
    title_h2 = doc.select_one("main h2")
    if title_h2:
        el = title_h2.find_next_sibling("p")
        if el and (t := _text(el)):
            if _LOCATION_KEYWORDS.search(t):
                return t
    return slug_to_location(urlparse(url).path)


def _openai_compensation(doc: BeautifulSoup, url: str) -> str | None:
    for el in doc.select("main p"):
        t = (el.get_text() or "").strip()
        if t.startswith("$"):
            return t
    return None


def _greenhouse_company(doc: BeautifulSoup, url: str) -> str | None:
    # boards.greenhouse.io/<company>/jobs/<id> — extract from path
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 1 and parts[0] not in ("jobs",):
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _greenhouse_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job__location")
    return _text(el)


# ---------------------------------------------------------------------------
# Workday site adapter — myworkdayjobs.com
# URL: <company>.wd1.myworkdayjobs.com/en-US/<tenant>/job/<location>/<title>_<id>
# ---------------------------------------------------------------------------


def _workday_company(doc: BeautifulSoup, url: str) -> str | None:
    # Extract company from subdomain: acme.wd1.myworkdayjobs.com → Acme
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www",):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _workday_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='jobPostingTitle']")
    if t := _text(el):
        return t
    # Some Workday tenants don't render the nested jobPostingTitle element and
    # only have the job title text directly in the jobPostingHeader heading.
    return _text(doc.select_one("[data-automation-id='jobPostingHeader']"))


def _workday_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='location']")
    if t := _text(el):
        return t
    # Some Workday tenants render locations as a <dl><dt>locations</dt><dd>...</dd>...</dl>
    # list (one <dd> per location) instead of a single nested "location" element.
    dds = doc.select("[data-automation-id='locations'] dd")
    if dds:
        return "; ".join(t for dd in dds if (t := _text(dd)))
    return None


def _workday_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='job-posting-details']")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Ashby site adapter — jobs.ashbyhq.com
# URL: jobs.ashbyhq.com/<company>/<job-id>
# ---------------------------------------------------------------------------


def _ashby_company(doc: BeautifulSoup, url: str) -> str | None:
    # Extract company from URL path: jobs.ashbyhq.com/figma/... → Figma
    parts = urlparse(url).path.strip("/").split("/")
    if parts and parts[0]:
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _ashby_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ashby-job-posting-heading, .ashby-job-posting-brief-description h1")
    return _text(el)


def _ashby_location(doc: BeautifulSoup, url: str) -> str | None:
    # Current markup: left pane has <h2>Location</h2><p>San Francisco</p> sections
    for section in doc.select(
        ".ashby-job-posting-left-pane ._section_101oc_37, .ashby-job-posting-left-pane [class*='_section']"
    ):
        h2 = section.find("h2")
        if h2 and "location" in (h2.get_text() or "").lower():
            p = section.find("p")
            if p and (t := _text(p)):
                return t
    # Fallback: legacy brief-description items
    items = doc.select(".ashby-job-posting-brief-description-item")
    if items:
        return _text(items[0])
    return None


def _ashby_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ashby-job-posting-description")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Lever site adapter — jobs.lever.co/<company>/<job-id>
# Page structure: div.posting-headline > h2 (title) + div.posting-categories
#                   > div[0]=location, div[1]=team, div[2]=commitment, div[3]=worktype
#                 div.section-wrapper > (job description sections)
# Note: Lever escapes class names in HTML so CSS selectors fail; navigate by position.
# ---------------------------------------------------------------------------


def _lever_company(doc: BeautifulSoup, url: str) -> str | None:
    # Prefer "Company - Job Title" in <title> tag for canonical casing
    title_tag = doc.find("title")
    if title_tag:
        raw = (title_tag.get_text() or "").strip()
        parts = raw.split(" - ", 1)
        if len(parts) == 2:
            return parts[0].strip() or None
    # Fallback: extract from URL path jobs.lever.co/<company>/<id>
    parts = urlparse(url).path.strip("/").split("/")
    if parts and parts[0]:
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _lever_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.find("h2"))


def _lever_location(doc: BeautifulSoup, url: str) -> str | None:
    h2 = doc.find("h2")
    if h2:
        cats = h2.find_next_sibling("div")
        if cats:
            divs = cats.find_all("div", recursive=False)
            if divs:
                return _text(divs[0])
    return None


def _lever_role_type(doc: BeautifulSoup, url: str) -> str | None:
    h2 = doc.find("h2")
    if h2:
        cats = h2.find_next_sibling("div")
        if cats:
            divs = cats.find_all("div", recursive=False)
            if len(divs) >= 3:
                raw = _text(divs[2]) or ""
                raw = raw.rstrip(" /").lower()
                if "full" in raw:
                    return "full-time"
                if "part" in raw:
                    return "part-time"
                if "contract" in raw:
                    return "contract"
                if "intern" in raw:
                    return "internship"
    return None


def _lever_description(doc: BeautifulSoup, url: str) -> str | None:
    # Lever wraps job content in div.section-wrapper.page-full-width (not accent-section/main-header).
    # class values may be HTML-escaped (e.g. '"section-wrapper"') in some fixtures; use substring match.
    for div in doc.find_all("div"):
        classes_str = " ".join(str(c) for c in div.get("class") or [])
        if "section-wrapper" not in classes_str:
            continue
        if "accent-section" in classes_str or "main-header" in classes_str:
            continue
        text = div.get_text(strip=True)
        if len(text) > 50:
            return _to_markdown(div)
    return None


# ---------------------------------------------------------------------------
# Cursor site adapter — cursor.com/careers/<slug>
# Page structure: main > article > div > header > h1 + p (dept·type·location)
#                                       div > div.prose (description)
# ---------------------------------------------------------------------------


def _cursor_location(doc: BeautifulSoup, url: str) -> str | None:
    # "Engineering · Full-time · San Francisco; New York" — take last segment
    p = doc.select_one("main article header p")
    if p and (t := _text(p)):
        parts = [x.strip() for x in t.split("·")]
        if len(parts) >= 3:
            return parts[-1] or None
    return None


def _cursor_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".prose")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Pinecone site adapter — pinecone.io/careers/<uuid>/
# Page structure: main > div > div > div.container.py-50 >
#                   a(All Jobs), h1, p("at Company, Location"), div(desc), div(apply)
# ---------------------------------------------------------------------------


def _pinecone_company(doc: BeautifulSoup, url: str) -> str | None:
    # "at Pinecone, New York City" — extract company name
    p = doc.select_one("main p")
    if p and (t := _text(p)):
        m = re.match(r"at\s+(.+?),\s+.+", t.strip())
        if m:
            return m.group(1).strip() or None
    return "Pinecone"


def _pinecone_location(doc: BeautifulSoup, url: str) -> str | None:
    # "at Pinecone, New York City" — extract location after company
    p = doc.select_one("main p")
    if p and (t := _text(p)):
        m = re.match(r"at\s+.+?,\s+(.+)", t.strip())
        if m:
            return m.group(1).strip() or None
    return None


def _pinecone_description(doc: BeautifulSoup, url: str) -> str | None:
    container = doc.select_one("main div.container, main div[class*='py-50']")
    if container:
        for div in container.find_all("div", recursive=False):
            t = _text(div)
            if t and len(t) > 100:
                return _to_markdown(div)
    return None


# ---------------------------------------------------------------------------
# Workable site adapter — jobs.workable.com/en/view/<id>/<slug> and
# apply.workable.com/<company-slug>/j/<id> (company-hosted "Apply" link).
# All fields live in a JSON-LD <script type="application/ld+json"> block.
# employmentType values: FULL_TIME, PART_TIME, CONTRACTOR, INTERN
# jobLocationType: TELECOMMUTE → "Remote"
# jobLocation is a single object on jobs.workable.com but a list on
# apply.workable.com — _workable_job_location() normalizes both.
# ---------------------------------------------------------------------------


def _workable_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    import json as _json

    for s in doc.find_all("script", type="application/ld+json"):
        try:
            d = _json.loads(s.string or "")
            if d.get("@type") == "JobPosting":
                return d  # type: ignore[no-any-return]
        except Exception:
            pass
    return {}


def _workable_title(doc: BeautifulSoup, url: str) -> str | None:
    return _workable_jsonld(doc).get("title") or None


def _workable_company(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    return (d.get("hiringOrganization") or {}).get("name") or None


def _workable_job_location(d: dict[str, Any]) -> dict[str, Any]:
    # jobLocation is a single object on jobs.workable.com but a list on
    # apply.workable.com — normalize to the first entry either way.
    job_location = d.get("jobLocation") or {}
    if isinstance(job_location, list):
        job_location = job_location[0] if job_location else {}
    return job_location


def _workable_location(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    if d.get("jobLocationType") == "TELECOMMUTE":
        addr = _workable_job_location(d).get("address") or {}
        city = addr.get("addressLocality", "")
        return f"{city} (Remote)" if city else "Remote"
    addr = _workable_job_location(d).get("address") or {}
    city = addr.get("addressLocality", "")
    region = addr.get("addressRegion", "")
    if city and region:
        return f"{city}, {region}"
    return city or region or None


def _workable_description(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    raw = d.get("description") or ""
    if not raw:
        return None
    return _to_markdown(BeautifulSoup(raw, "lxml"))


def _workable_role_type(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    emp = (d.get("employmentType") or "").upper()
    return {
        "FULL_TIME": "full-time",
        "PART_TIME": "part-time",
        "CONTRACTOR": "contract",
        "INTERN": "internship",
    }.get(emp)


# ---------------------------------------------------------------------------
# Databricks site adapter — databricks.com/company/careers/...
# ---------------------------------------------------------------------------


def _databricks_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1:
        sib = h1.find_next_sibling()
        if sib:
            # Remove the "Apply now" button text
            for btn in sib.find_all("button"):
                btn.decompose()
            return _text(sib)
    return None


def _databricks_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Notion site adapter — <company>.notion.site/<page-id>
# Notion public pages render React-driven HTML. Key signals:
#   - Company name: URL subdomain, with casing from topbar breadcrumb
#   - Title: <title> tag / og:title (reliable)
#   - Properties (Location, Employment Type, Department): extracted from
#     the flat text stream because Notion generates anonymous class names.
#     Properties appear as consecutive lines: "Location\nRemote\nSan Francisco\n..."
#     terminated by the next property name or by "What we do" / page content.
#   - Description: .notion-page-content text (starts after property block)
# ---------------------------------------------------------------------------

_NOTION_PROPERTY_NAMES = {
    "Department",
    "Employment Type",
    "Location",
    "Created",
    "Last edited time",
}

_NOTION_PROPERTY_HEADINGS = {
    "What we do",
    "What we want",
    "What you want",
    "What you've done",
    "About the role",
    "About us",
    "About you",
    "Requirements",
    "Responsibilities",
    "Qualifications",
    "Benefits",
    "Compensation",
}


def _notion_text_lines(doc: BeautifulSoup) -> list[str]:
    return [line.strip() for line in doc.get_text(separator="\n").split("\n") if line.strip()]


def _notion_company(doc: BeautifulSoup, url: str) -> str | None:
    # Prefer topbar breadcrumb first page-block for canonical casing
    topbar = doc.select_one(".notion-topbar")
    if topbar:
        page_block = topbar.select_one(".notion-page-block")
        if page_block and (t := _text(page_block)):
            # "ParadeDB Job Board" → strip trailing " Job Board" / " Careers" etc.
            name = re.sub(
                r"\s+(Job Board|Careers?|Jobs?|Opportunities)\s*$", "", t, flags=re.IGNORECASE
            )
            if name:
                return name.strip()
    # Fallback: subdomain of notion.site URL
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www", "notion"):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _notion_property_value(doc: BeautifulSoup, prop: str) -> str | None:
    lines = _notion_text_lines(doc)
    try:
        idx = lines.index(prop)
    except ValueError:
        return None
    # Collect value lines until the next property name or page-content heading
    values: list[str] = []
    for line in lines[idx + 1 :]:
        if line in _NOTION_PROPERTY_NAMES or line in _NOTION_PROPERTY_HEADINGS:
            break
        values.append(line)
    return ", ".join(values) if values else None


def _notion_location(doc: BeautifulSoup, url: str) -> str | None:
    return _notion_property_value(doc, "Location")


def _notion_role_type(doc: BeautifulSoup, url: str) -> str | None:
    raw = (_notion_property_value(doc, "Employment Type") or "").lower()
    if not raw:
        return _generic_role_type(doc, url)
    if "full" in raw:
        return "full-time"
    if "part" in raw:
        return "part-time"
    if "contract" in raw:
        return "contract"
    if "intern" in raw:
        return "internship"
    return None


def _notion_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".notion-page-content")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Pinterest careers site adapter — pinterestcareers.com/jobs/<id>/<slug>/
# Custom wrapper around Greenhouse. Page structure:
#   main > ... > first <li> = "San Francisco / Palo Alto / Seattle" (location)
#              > second <li> = team, third <li> = employment type
#   h1 = job title (generic handles this)
# ---------------------------------------------------------------------------


def _pinterest_location(doc: BeautifulSoup, url: str) -> str | None:
    # First <li> in main contains the location string
    for li in doc.select("main li"):
        t = _text(li)
        if t and t not in ("", "Regular", "Temporary"):
            return t
    return None


def _pinterest_role_type(doc: BeautifulSoup, url: str) -> str | None:
    # Third <li> in main is employment type: "Regular" → full-time, "Temporary" → contract
    lis = [li for li in doc.select("main li") if _text(li)]
    if len(lis) >= 3:
        raw = (_text(lis[2]) or "").lower()
        if "regular" in raw:
            return "full-time"
        if "temporary" in raw:
            return "contract"
        if "intern" in raw:
            return "internship"
    return None


def _pinterest_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# AdaL (adalagent.ai) — custom React SPA; location in subtitle paragraph
# ---------------------------------------------------------------------------


def _adal_location(doc: BeautifulSoup, url: str) -> str | None:
    # Subtitle: "SylphAI. San Francisco, United States." — drop the company prefix
    el = doc.select_one("p.text-adal-text-secondary, p.italic")
    if not el:
        return None
    text = _text(el) or ""
    # Strip leading "SylphAI. " (or any "Word. " prefix before the location)
    parts = text.split(". ", 1)
    location = parts[1] if len(parts) == 2 else text
    return location.rstrip(".").strip() or None


def _adal_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Larridin (larridin.com) — HubSpot CMS page. Job header is a ".headings" div
# (h1 title) followed by a sibling ".col-content" div holding the location
# paragraph. Job body content lives in one or more ".sr-richtext" divs.
# ---------------------------------------------------------------------------


def _larridin_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if not h1:
        return None
    headings = h1.find_parent("div", class_="headings")
    if not headings:
        return None
    col_content = headings.find_next_sibling("div", class_="col-content")
    return _text(col_content)


def _larridin_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [md for el in doc.select(".sr-richtext") if (md := _to_markdown(el))]
    return "\n\n".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Airbnb careers site — careers.airbnb.com/positions/<id>
# Page structure: h1 (title), next sibling text node = location,
#                 main section paragraphs = description
# ---------------------------------------------------------------------------


def _airbnb_location(doc: BeautifulSoup, url: str) -> str | None:
    # Location is in the first div sibling after h1
    h1 = doc.select_one("h1")
    if h1:
        el = h1.find_next_sibling("div")
        if el and (t := _text(el)):
            return t
    return None


def _airbnb_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("#job-detail-panel, .job-detail")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Discord (discord.com/jobs/<id>) — custom React SPA
# ---------------------------------------------------------------------------


def _discord_location(doc: BeautifulSoup, url: str) -> str | None:
    # Location lives in a div with class containing "heroLocation"
    el = doc.select_one('[class*="heroLocation"]')
    return _text(el)


def _discord_description(doc: BeautifulSoup, url: str) -> str | None:
    # Job body container has class "body-" and "section-" and "document-"
    el = doc.select_one('[class*="body-"][class*="section-"]')
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Stripe site adapter — stripe.com/jobs/listing/<slug>/<id>
# Page structure: persistent header has its own <h1>, so a bare "h1" selector
# grabs "Stripe logo Jobs" instead of the job title. Job title is the first
# h1.Copy__title inside .Copy__header. Office locations/Team/Job type are
# label/value pairs under .JobDetailCardProperty__title. Description body is
# the .ArticleMarkdown container.
# ---------------------------------------------------------------------------


def _stripe_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".Copy__header h1"))


def _stripe_location(doc: BeautifulSoup, url: str) -> str | None:
    for label in doc.select(".JobDetailCardProperty__title"):
        if (label.get_text(strip=True) or "").lower() == "office locations":
            sib = label.find_next_sibling()
            if sib and (t := _text(sib)):
                return t
    return None


def _stripe_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ArticleMarkdown")
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Apple site adapter — jobs.apple.com/en-us/details/<id>/<slug>
# Page structure: h1 = job title (generic handles this). Location and team
# are sibling <label> elements (#jobdetails-joblocation / #jobdetails-teamname)
# in the row right after the h1. Job content is split across sibling
# div#jobdetails-* sections (Summary, Description, Responsibilities,
# Qualifications, Pay & Benefits, plus unheaded legal-boilerplate footers);
# only the headed sections are joined for the description.
# ---------------------------------------------------------------------------


def _apple_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("#jobdetails-joblocation"))


def _apple_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = []
    for div in doc.select("section.hyperlink-underline > div[id^='jobdetails-']"):
        if div.find("h2") and (md_text := _to_markdown(div)):
            parts.append(md_text)
    return "\n\n".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Turing site adapter — careers.turing.com/job/<id>
# Page structure: div[class*="job-details-title"] = job title
#                 div[class*="job-details-location"] = "Location: <cities>"
#                 div[class*="job-details-description"] = full job description
# ---------------------------------------------------------------------------


def _turing_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="job-details-title"]')
    return _text(el)


def _turing_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="job-details-location"]')
    if not el:
        return None
    t = _text(el) or ""
    # Strip "Location: " prefix
    if t.lower().startswith("location:"):
        t = t[len("location:") :].strip()
    return t or None


def _turing_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="job-details-description"]')
    return _to_markdown(el)


# ---------------------------------------------------------------------------
# Hacker News site adapter — news.ycombinator.com/item?id=<comment-id>
# Single-comment page layout: table.fatitem > tr.athing > td.default >
#   div.comment > div.commtext
# Dead/flagged comments have class "cdd" or "cdf" on the commtext element.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TikTok / lifeattiktok.com site adapter
# Detail page structure (React SPA, CSS-Module class names):
#   .job-header > [data-test="jobTitle"]         = job title
#   .job-info   > span[0] > span.clamp-content   = location (e.g. "San Jose")
#   .job-info   > span[1]                        = employment type ("Regular" = full-time)
#   .block-title / .block-content pairs          = description sections
# ---------------------------------------------------------------------------


def _tiktok_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('[data-test="jobTitle"]'))


def _tiktok_location(doc: BeautifulSoup, url: str) -> str | None:
    job_info = doc.select_one(".job-info")
    if not job_info:
        return None
    for span in job_info.find_all("span", recursive=False):
        if t := _text(span):
            return t
    return None


def _tiktok_role_type(doc: BeautifulSoup, url: str) -> str | None:
    job_info = doc.select_one(".job-info")
    if job_info:
        spans = [s for s in job_info.find_all("span", recursive=False) if _text(s)]
        if len(spans) >= 2:
            raw = (_text(spans[1]) or "").lower()
            if "regular" in raw:
                return "full-time"
            if "intern" in raw:
                return "internship"
            if "contract" in raw:
                return "contract"
    return _generic_role_type(doc, url)


def _tiktok_description(doc: BeautifulSoup, url: str) -> str | None:
    parts: list[str] = []
    for el in doc.select(".block-title, .block-content"):
        classes = el.get_attribute_list("class")
        if "block-title" in classes:
            parts.append(f"\n## {_text(el)}\n")
        elif "block-content" in classes:
            if md_part := _to_markdown(el):
                parts.append(md_part)
    return "\n".join(parts).strip() or None


# ---------------------------------------------------------------------------
# Waymo site adapter — careers.withwaymo.com/jobs/<slug>
# Generic "h1, main h2" selectors hit unrelated sitewide headings ("Working
# at Waymo", "Teams") before the real job title, and the generic
# [class*="location"] selector matches a related-job sidebar link instead of
# this job's own location. Title/location must be scoped to
# .block-job-description, which wraps just this job's own content.
# ---------------------------------------------------------------------------


def _waymo_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".block-job-description h3.job-title"))


def _waymo_location(doc: BeautifulSoup, url: str) -> str | None:
    els = doc.select(".block-job-description .job-component-location")
    parts = [t for el in els if (t := _text(el))]
    return ", ".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Google Careers site adapter — google.com/about/careers/applications/jobs/results/<slug>
# Angular SPA: the sitewide <h1> is a generic "job details" label, and a
# "Jobs search results" <h2> in the sidebar list precedes the real job <h2>
# in some layouts, so generic selectors miss the actual title/company.
# Location renders as a Material Icon ligature ("place") followed by a
# sibling <span> with the value, not plain text a CSS class can target.
# The job's own content lives in a <div data-id="..."> ancestor of the
# title <h2>; description rows sit between the "Apply" row and the trailing
# EEO/privacy boilerplate row.
# ---------------------------------------------------------------------------


def _google_careers_container(doc: BeautifulSoup) -> Tag | None:
    h2 = doc.select_one("main h2")
    if h2 is None:
        return None
    node = h2.parent
    while node is not None:
        if node.has_attr("data-id"):
            return node
        node = node.parent
    return None


def _google_careers_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("main h2"))


def _google_careers_location(doc: BeautifulSoup, url: str) -> str | None:
    main = doc.find("main")
    if main is None:
        return None
    icon = next((i for i in main.find_all("i") if (i.get_text() or "").strip() == "place"), None)
    if icon is None:
        return None
    return _text(icon.find_next_sibling("span"))


def _google_careers_description(doc: BeautifulSoup, url: str) -> str | None:
    container = _google_careers_container(doc)
    if container is None:
        return None
    started = False
    parts = []
    for child in container.find_all("div", recursive=False):
        text = child.get_text(" ", strip=True)
        if not text:
            continue
        if not started:
            if "Apply" in text:
                started = True
            continue
        if "Privacy Policy" in text or "equal opportunity" in text.lower():
            break
        if md_part := _to_markdown(child):
            parts.append(md_part)
    return "\n\n".join(parts) if parts else None


def _wbd_location(doc: BeautifulSoup, url: str) -> str | None:
    # Multi-location postings list one .location element per location; a plain
    # select_one would only capture the first, dropping the rest.
    seen: list[str] = []
    for el in doc.select(".location.au-target"):
        if (t := _text(el)) and t not in seen:
            seen.append(t)
    return "; ".join(seen) if seen else None


# ---------------------------------------------------------------------------
# C3.ai (c3.ai) — Next.js job page. Title is a bare <h1>, location/department
# share one <p> right after it ("City, ST · Department"), and the full JD
# lives in the wrapper <div> that follows the "Apply Now" button.
# ---------------------------------------------------------------------------


def _c3ai_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    p = h1.find_next_sibling("p")
    if p is None:
        return None
    text = _text(p) or ""
    location = text.split("·", 1)[0].strip()
    return location or None


def _c3ai_description(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    button = h1.find_next_sibling("button")
    if button is None:
        return None
    wrapper = button.find_next_sibling("div")
    return _to_markdown(wrapper)


# ---------------------------------------------------------------------------
# Rippling ATS (ats.rippling.com/<company-slug>/jobs/<id>) — shared job board
# used by many companies. The recruiter-authored description sometimes
# embeds the next section's heading inside the same <h1> as the job title
# (via a nested <strong>), so title comes from the document <title> tag
# instead. There's no structured company-name field on the page; it's
# derived from the breadcrumb link back to the employer's own careers site
# (may need casing fixes via merge_companies after ingest).
# ---------------------------------------------------------------------------


def _rippling_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.title) if doc.title else None


def _rippling_company(doc: BeautifulSoup, url: str) -> str | None:
    breadcrumb = doc.select_one('a[data-testid^="http"]')
    if breadcrumb is None:
        return None
    href = breadcrumb.get("data-testid") or ""
    host = (urlparse(str(href)).hostname or "").removeprefix("www.")
    label = host.split(".")[0]
    return label.replace("-", " ").title() or None


def _rippling_location(doc: BeautifulSoup, url: str) -> str | None:
    icon = doc.select_one('span[data-icon="LOCATION_OUTLINE"]')
    if icon is None:
        return None
    return _text(icon.find_next_sibling("p"))


def _rippling_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".ATS_htmlPreview"))


# ---------------------------------------------------------------------------
# Twilio (jobs.twilio.com) — Eightfold-powered ATS hosted on Twilio's own
# domain. The static <h1> always reads "Single Position" no matter which job
# is loaded; the real title is in an <h2> further down (CSS-module class
# names are hashed per build, so match on the stable prefix instead).
# ---------------------------------------------------------------------------


def _twilio_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('h2[class*="position-title"]'))


def _twilio_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('div[class*="position-location"]'))


def _twilio_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("#job-description-container"))


# ---------------------------------------------------------------------------
# Nebius (careers.nebius.com) — the real job description/apply flow is a
# cross-origin Greenhouse iframe scout_fetch can't see, so scout_fetch
# fetches Greenhouse's public Jobs API instead and hands this adapter
# synthetic HTML with the fields under fixed classes (see
# jobforce.cli.scout_fetch._fetch_nebius_greenhouse_html).
# ---------------------------------------------------------------------------


def _nebius_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".nebius-gh-title"))


def _nebius_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".nebius-gh-location"))


def _nebius_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".nebius-gh-description"))


# ---------------------------------------------------------------------------
# Asana (asana.com/jobs/apply/<id>) — title already extracts correctly via
# the generic adapter's <h1> selector; company_name, location, and
# description need overrides since CSS-module class names are hashed per
# build. The description div is the sibling right after the div holding the
# "#grnhse_app" apply anchor (Asana embeds a Greenhouse apply widget there).
# ---------------------------------------------------------------------------


def _asana_location(doc: BeautifulSoup, url: str) -> str | None:
    main = doc.select_one("main")
    return _text(main.select_one("h4")) if main else None


def _asana_description(doc: BeautifulSoup, url: str) -> str | None:
    apply_link = doc.select_one('a[href^="#grnhse_app"]')
    if apply_link is None:
        return None
    apply_container = apply_link.find_parent("div")
    if apply_container is None:
        return None
    desc_div = apply_container.find_next_sibling("div")
    return _to_markdown(desc_div)


# ---------------------------------------------------------------------------
# Breezy HR (<company>.breezy.hr/p/<id>-<slug>) — shared ATS matched by
# hostname suffix. The page has two <h1>s (the site brand/logo, then the
# real job title), so the generic adapter's bare "h1" selector grabs the
# wrong one. Company name comes from the subdomain, mirroring the Workday
# adapter's approach.
# ---------------------------------------------------------------------------


def _breezy_company(doc: BeautifulSoup, url: str) -> str | None:
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www",):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _breezy_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".banner h1"))


# ---------------------------------------------------------------------------
# Block (block.xyz/careers/jobs/<id>) — the site's own og:site_name meta is
# buggy and echoes the page title instead of "Block", so the generic
# adapter's company_name fallback grabs the wrong text.
# ---------------------------------------------------------------------------


def _block_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('[data-testid="job-location"]'))


def _block_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one('[data-testid="job-about"]'))


# ---------------------------------------------------------------------------
# Brex (brex.com/careers/<id>) — title and company_name already extract
# correctly via the generic adapter. Brex renders Greenhouse's job content
# HTML directly, including its ".content-intro" wrapper div, so the
# description container is that div's parent.
# ---------------------------------------------------------------------------


def _brex_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h4"))


def _brex_description(doc: BeautifulSoup, url: str) -> str | None:
    intro = doc.select_one(".content-intro")
    if intro is None:
        return None
    container = intro.find_parent("div")
    return _to_markdown(container)


# ---------------------------------------------------------------------------
# Chime (careers.chime.com/jobs/<id>/<slug>) — title extracts fine via the
# generic adapter's <h1>. Location is the second of two <p> tags inside
# ".content-wrapper" (department, then location); description lives in the
# ".jobCopy" container.
# ---------------------------------------------------------------------------


def _chime_location(doc: BeautifulSoup, url: str) -> str | None:
    ps = doc.select(".content-wrapper p")
    if len(ps) < 2:
        return None
    return _text(ps[1])


def _chime_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".jobCopy"))


# ---------------------------------------------------------------------------
# Coinbase (coinbase.com/careers/positions/<id>) — title extracts fine via
# the generic adapter's <h1>. Location is the first of two <span> tags in
# the div right after the <h1>. Coinbase renders Greenhouse's job content
# HTML directly, including its ".content-intro" wrapper div, so the
# description container is that div's parent — same pattern as Brex.
# ---------------------------------------------------------------------------


def _coinbase_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    sib = h1.find_next_sibling("div")
    if sib is None:
        return None
    return _text(sib.select_one("span"))


def _coinbase_description(doc: BeautifulSoup, url: str) -> str | None:
    intro = doc.select_one(".content-intro")
    if intro is None:
        return None
    container = intro.find_parent("div")
    return _to_markdown(container)


# ---------------------------------------------------------------------------
# Intuit (jobs.intuit.com) — shared board across all Intuit brands (Credit
# Karma, TurboTax, QuickBooks, Mailchimp). Title extracts fine via the
# generic adapter's <h1>, which carries a " - <Brand>" suffix company_name is
# derived from (falls back to "Intuit" for postings with no such suffix).
# The generic adapter's location falls back to page-level "Multiple
# Locations" metadata instead of the real ".job-location-jd" element.
# ---------------------------------------------------------------------------


def _intuit_company(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    text = _text(h1) or ""
    if " - " in text:
        return text.rsplit(" - ", 1)[-1].strip() or "Intuit"
    return "Intuit"


def _intuit_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job-location-jd")
    if el is None:
        return None
    text = _text(el) or ""
    text = re.sub(r"^Location\s*", "", text)
    text = re.sub(r"\s*;\s*", "; ", text)
    return text.strip() or None


SITE_ADAPTERS: dict[str, dict[str, Any]] = {
    "careers.airbnb.com": {
        "company_name": lambda doc, url: "Airbnb",
        "location": _airbnb_location,
        "description": _airbnb_description,
    },
    "adalagent.ai": {
        "company_name": lambda doc, url: "AdaL",
        "location": _adal_location,
        "description": _adal_description,
    },
    "larridin.com": {
        "company_name": lambda doc, url: "Larridin",
        "location": _larridin_location,
        "description": _larridin_description,
    },
    "c3.ai": {
        "company_name": lambda doc, url: "C3 AI",
        "location": _c3ai_location,
        "description": _c3ai_description,
    },
    "ats.rippling.com": {
        "title": _rippling_title,
        "company_name": _rippling_company,
        "location": _rippling_location,
        "description": _rippling_description,
    },
    "discord.com": {
        "company_name": lambda doc, url: "Discord",
        "location": _discord_location,
        "description": _discord_description,
    },
    "jobs.lever.co": {
        "company_name": _lever_company,
        "title": _lever_title,
        "location": _lever_location,
        "role_type": _lever_role_type,
        "description": _lever_description,
    },
    "openai.com": {
        "company_name": lambda doc, url: "OpenAI",
        "title": lambda doc, url: _text(doc.select_one("main h2")),
        "location": _openai_location,
        "description": lambda doc, url: _to_markdown(
            doc.select_one("main article, main section, main div")
        ),
        "compensation": _openai_compensation,
    },
    "boards.greenhouse.io": {
        "company_name": _greenhouse_company,
        "location": _greenhouse_location,
    },
    "job-boards.greenhouse.io": {
        "company_name": _greenhouse_company,
        "location": _greenhouse_location,
    },
    "myworkdayjobs.com": {
        "company_name": _workday_company,
        "title": _workday_title,
        "location": _workday_location,
        "description": _workday_description,
    },
    "jobs.ashbyhq.com": {
        "company_name": _ashby_company,
        "title": _ashby_title,
        "location": _ashby_location,
        "description": _ashby_description,
    },
    "databricks.com": {
        "company_name": lambda doc, url: "Databricks",
        "location": _databricks_location,
        "description": _databricks_description,
    },
    "cursor.com": {
        "company_name": lambda doc, url: "Cursor",
        "location": _cursor_location,
        "description": _cursor_description,
    },
    "pinecone.io": {
        "company_name": _pinecone_company,
        "location": _pinecone_location,
        "description": _pinecone_description,
    },
    "jobs.workable.com": {
        "company_name": _workable_company,
        "title": _workable_title,
        "location": _workable_location,
        "description": _workable_description,
        "role_type": _workable_role_type,
    },
    "apply.workable.com": {
        "company_name": _workable_company,
        "title": _workable_title,
        "location": _workable_location,
        "description": _workable_description,
        "role_type": _workable_role_type,
    },
    "pinterestcareers.com": {
        "company_name": lambda doc, url: "Pinterest",
        "location": _pinterest_location,
        "role_type": _pinterest_role_type,
        "description": _pinterest_description,
    },
    "notion.site": {
        "company_name": _notion_company,
        "location": _notion_location,
        "role_type": _notion_role_type,
        "description": _notion_description,
    },
    "stripe.com": {
        "company_name": lambda doc, url: "Stripe",
        "title": _stripe_title,
        "location": _stripe_location,
        "description": _stripe_description,
    },
    "jobs.apple.com": {
        "company_name": lambda doc, url: "Apple",
        "location": _apple_location,
        "description": _apple_description,
    },
    "careers.turing.com": {
        "company_name": lambda doc, url: "Turing",
        "title": _turing_title,
        "location": _turing_location,
        "description": _turing_description,
    },
    "lifeattiktok.com": {
        "company_name": lambda doc, url: "TikTok",
        "title": _tiktok_title,
        "location": _tiktok_location,
        "role_type": _tiktok_role_type,
        "description": _tiktok_description,
    },
    "careers.withwaymo.com": {
        "company_name": lambda doc, url: "Waymo",
        "title": _waymo_title,
        "location": _waymo_location,
    },
    "google.com": {
        "company_name": lambda doc, url: "Google",
        "title": _google_careers_title,
        "location": _google_careers_location,
        "description": _google_careers_description,
    },
    "careers.wbd.com": {
        "company_name": lambda doc, url: "Warner Bros. Discovery",
        "location": _wbd_location,
        "description": lambda doc, url: _to_markdown(doc.select_one(".jd-info")),
    },
    "jobs.twilio.com": {
        "company_name": lambda doc, url: "Twilio",
        "title": _twilio_title,
        "location": _twilio_location,
        "description": _twilio_description,
    },
    "careers.nebius.com": {
        "company_name": lambda doc, url: "Nebius",
        "title": _nebius_title,
        "location": _nebius_location,
        "description": _nebius_description,
    },
    "asana.com": {
        "company_name": lambda doc, url: "Asana",
        "location": _asana_location,
        "description": _asana_description,
    },
    "breezy.hr": {
        "company_name": _breezy_company,
        "title": _breezy_title,
    },
    "block.xyz": {
        "company_name": lambda doc, url: "Block",
        "location": _block_location,
        "description": _block_description,
    },
    "brex.com": {
        "location": _brex_location,
        "description": _brex_description,
    },
    "careers.chime.com": {
        "company_name": lambda doc, url: "Chime",
        "location": _chime_location,
        "description": _chime_description,
    },
    "coinbase.com": {
        "company_name": lambda doc, url: "Coinbase",
        "location": _coinbase_location,
        "description": _coinbase_description,
    },
    "jobs.intuit.com": {
        "company_name": _intuit_company,
        "location": _intuit_location,
    },
}

# ---------------------------------------------------------------------------
# Framework
# ---------------------------------------------------------------------------


def run_adapter(adapter: dict[str, Any], doc: BeautifulSoup, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, fn in adapter.items():
        try:
            result[key] = fn(doc, url)
        except Exception:
            logger.warning("[parse] adapter field %r error", key, exc_info=True)
            result[key] = None
    return result


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if v is not None and v != "":
            out[k] = v
    return out


def _match_adapter(hostname: str) -> dict[str, Any]:
    if hostname in SITE_ADAPTERS:
        return SITE_ADAPTERS[hostname]
    # suffix match for subdomain-based ATSes (e.g. acme.wd1.myworkdayjobs.com)
    for key, adapter in SITE_ADAPTERS.items():
        if hostname.endswith("." + key):
            return adapter
    return {}


def parse_html(html: str, url: str) -> dict[str, Any]:
    hostname = (urlparse(url).hostname or "").removeprefix("www.")
    if hostname == "news.ycombinator.com":
        return _parse_hn(html, url)
    doc = BeautifulSoup(html, "lxml")
    adapter = _match_adapter(hostname)
    base = run_adapter(GENERIC_ADAPTER, doc, url)
    override = run_adapter(adapter, doc, url) if adapter else {}
    return {"source_url": url, **merge(base, override)}
