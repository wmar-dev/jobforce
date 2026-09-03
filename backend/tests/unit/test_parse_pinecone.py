"""Unit tests for the Pinecone (pinecone.io/careers/<uuid>/) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_pinecone_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["title"] == "Senior/Staff Software Engineer, Database Team"


def test_parse_html_pinecone_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["company_name"] == "Pinecone"


def test_parse_html_pinecone_location_from_at_p() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["location"] == "New York City"


def test_parse_html_pinecone_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["description"] is not None
    assert "Pinecone" in result["description"]
