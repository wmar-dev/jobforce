"""Unit tests for the ArgusEye (arguseye.ai) site adapter — custom Next.js page;
company name is not in the markup as a dedicated field and location lives in a
``<dl>`` of ``<dt>``/``<dd>`` pairs.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ARGUSEYE_URL = "https://www.arguseye.ai/careers/cmq4tgc7q0002kz046bef5uod"


def test_parse_html_arguseye_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("arguseye_job.html"), _ARGUSEYE_URL)
    assert result["company_name"] == "ArgusEye"


def test_parse_html_arguseye_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("arguseye_job.html"), _ARGUSEYE_URL)
    assert result["location"] == "San Ramon, California"


def test_parse_html_arguseye_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("arguseye_job.html"), _ARGUSEYE_URL)
    assert result["description"] is not None
    assert "cybersecurity analysis" in result["description"]
