from __future__ import annotations

from jobforce.scripts.render_template import _build_env, latex_escape, latex_url


def test_latex_escape_specials() -> None:
    assert latex_escape("R&D 100% #1 a_b") == r"R\&D 100\% \#1 a\_b"
    assert latex_escape("\\{}") == r"\textbackslash{}\{\}"


def test_latex_escape_non_string() -> None:
    assert latex_escape(2021) == "2021"


def test_latex_url_escapes_only_href_breakers() -> None:
    assert latex_url("https://x.io/a_b?q=1%20#top") == r"https://x.io/a_b?q=1\%20\#top"


def test_template_escapes_urls_dates_and_years() -> None:
    data = {
        "personal_info": {"name": "A", "linkedin": "linkedin.com/in/a_b%c", "github": "a_b"},
        "work_history": [
            {"title": "Eng", "company": "Co", "start_date": "2020 #1", "end_date": None}
        ],
        "certifications": [{"name": "Cert", "year": 2021}],
        "projects": [{"name": "P", "url": "https://x.io/p#readme"}],
    }
    tex = _build_env().get_template("resume.tex.j2").render(data=data)

    assert r"\href{https://linkedin.com/in/a_b\%c}{linkedin.com/in/a\_b\%c}" in tex
    assert r"\href{https://github.com/a_b}{github.com/a\_b}" in tex
    assert r"2020 \#1 -- Present" in tex
    assert "(2021)" in tex
    assert r"\href{https://x.io/p\#readme}{https://x.io/p\#readme}" in tex
