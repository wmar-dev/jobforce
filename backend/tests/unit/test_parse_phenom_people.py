"""Unit tests for the Phenom People boards — Yelp (www.yelp.careers) and Adobe
(careers.adobe.com) share this ATS template. title and company_name already
extract fine via the generic adapter (h1 + og:site_name); location and
description do not. The page renders a duplicate, unfilled
"job-description"/".jd-info" template block alongside the real one (a Phenom
quirk), so description is pulled from the page's own schema.org JobPosting
JSON-LD block instead of that CSS selector. location isn't a single plain-text
element either — the JobPosting's jobLocation can be a single Place (Adobe) or
a list of them for multi-office reqs (Yelp) — so it's parsed from the page
<title>'s "job in <location> |" segment, which names the specific location this
URL represents. role_type comes from the JSON-LD employmentType list.

scout_fetch's fetch wait (`"h1, main h2"`, state="attached") also resolves
against this ATS's empty template h1 before Phenom's client-side hydration
fills it in, which is what left job 3106's title/location/description/role_type
all null on first crawl — see the _HYDRATION_WAIT_CONDITIONS entries for these
hosts in jobforce/cli/scout_fetch.py.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_YELP_URL = "https://www.yelp.careers/us/en/job/13815/Senior-Machine-Learning-Engineer-Content-and-Contributor-Intelligence-Remote-United-States"


def test_parse_html_yelp_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("yelp_job.html")
    result = parse_html(html, _YELP_URL)
    assert result["location"] == "San Francisco, California, United States"


def test_parse_html_yelp_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("yelp_job.html")
    result = parse_html(html, _YELP_URL)
    assert result["description"] is not None
    assert "cutting-edge Machine Learning" in result["description"]


def test_parse_html_yelp_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("yelp_job.html")
    result = parse_html(html, _YELP_URL)
    assert result["role_type"] == "full-time"


_ADOBE_URL = "https://careers.adobe.com/us/en/job/R169102/Machine-Learning-Engineer-5"


def test_parse_html_adobe_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adobe_job.html")
    result = parse_html(html, _ADOBE_URL)
    assert result["location"] == "San Jose, California, United States of America"


def test_parse_html_adobe_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adobe_job.html")
    result = parse_html(html, _ADOBE_URL)
    assert result["description"] is not None
    assert "Brand Intelligence Predict" in result["description"]


def test_parse_html_adobe_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adobe_job.html")
    result = parse_html(html, _ADOBE_URL)
    assert result["role_type"] == "full-time"


_CISCO_URL = "https://careers.cisco.com/global/en/job/2018923/Senior-AI-Researcher"


def test_parse_html_cisco_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cisco_job.html")
    result = parse_html(html, _CISCO_URL)
    assert result["title"] == "Senior AI Researcher"


def test_parse_html_cisco_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cisco_job.html")
    result = parse_html(html, _CISCO_URL)
    assert result["location"] == "San Francisco, California, United States of America"


def test_parse_html_cisco_description_full() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cisco_job.html")
    result = parse_html(html, _CISCO_URL)
    assert result["description"] is not None
    assert "Meet the Team" in result["description"]
    assert "leading frontier AI research across Cisco" in result["description"]


def test_parse_html_cisco_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cisco_job.html")
    result = parse_html(html, _CISCO_URL)
    assert result["role_type"] == "full-time"
