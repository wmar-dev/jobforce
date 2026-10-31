"""Unit tests for jobforce.cli.sync_target_companies."""

from __future__ import annotations

from pathlib import Path

import yaml

from jobforce.cli.sync_target_companies import merge

_TARGET = (
    '    - name: "Acme"\n'
    '      domain: "acme.com"  # keep this comment\n'
    '      careers_url: "https://acme.com/careers"\n'
    '    - name: "Zeta"\n'
    '      domain: "zeta.io"\n'
    '      careers_url: ""\n'
)


def _c(name: str, domain: str = "", careers_url: str = "") -> dict[str, str]:
    return {"name": name, "domain": domain, "careers_url": careers_url}


def test_adds_new_company_in_alphabetical_order() -> None:
    text, added, _ = merge(_TARGET, [_c("Mango", "mango.ai", "https://jobs.ashbyhq.com/mango")])

    assert added == ["Mango"]
    names = [e["name"] for e in yaml.safe_load(text)]
    assert names == ["Acme", "Mango", "Zeta"]


def test_existing_entries_kept_verbatim() -> None:
    text, _, _ = merge(_TARGET, [_c("Mango")])

    assert "# keep this comment" in text


def test_skips_names_already_present_after_normalizing() -> None:
    text, added, _ = merge(_TARGET, [_c("ACME"), _c("zeta")])

    assert added == []
    assert text == _TARGET


def test_skips_aggregator_urls() -> None:
    _, added, skipped = merge(
        _TARGET,
        [
            _c("Ask HN: Who Is Hiring?", careers_url="https://news.ycombinator.com/item?id=1"),
            _c("Sequoia Companies", "sequoiacap.com", "https://jobs.sequoiacap.com/jobs/"),
        ],
    )

    assert added == []
    assert skipped == {"Ask HN: Who Is Hiring?": "aggregator", "Sequoia Companies": "aggregator"}


def test_skips_company_whose_careers_url_is_already_listed() -> None:
    _, added, skipped = merge(
        _TARGET + '    - name: "The Bot Company"\n      domain: ""\n'
        '      careers_url: "https://jobs.ashbyhq.com/thebotcompany"\n',
        [
            _c("Bot Co", careers_url="https://jobs.ashbyhq.com/thebotcompany/"),
            _c("Portola", careers_url="https://www.tolans.com/careers"),
            _c("Tolan (Portola)", careers_url="https://www.tolans.com/careers"),
        ],
    )

    assert added == ["Portola"]
    assert skipped == {
        "Bot Co": "same careers_url as The Bot Company",
        "Tolan (Portola)": "same careers_url as Portola",
    }


def test_duplicate_config_entries_prefer_one_with_careers_url() -> None:
    text, added, _ = merge(_TARGET, [_c("Mango"), _c("Mango", careers_url="https://mango.ai/jobs")])

    assert added == ["Mango"]
    mango = [e for e in yaml.safe_load(text) if e["name"] == "Mango"]
    assert mango == [{"name": "Mango", "domain": "", "careers_url": "https://mango.ai/jobs"}]


def test_domain_url_is_normalized_and_quotes_escaped() -> None:
    text, _, _ = merge(_TARGET, [_c('Say "Hi"', "https://www.sayhi.ai/")])

    entry = [e for e in yaml.safe_load(text) if e["name"] == 'Say "Hi"'][0]
    assert entry["domain"] == "sayhi.ai"


def test_skip_name_only_drops_entries_without_url_or_domain() -> None:
    companies = [
        _c("Bare"),
        _c("Domained", "domained.ai"),
        _c("Urled", careers_url="https://u.io/jobs"),
    ]

    _, added, skipped = merge(_TARGET, companies, skip_name_only=True)
    assert added == ["Domained", "Urled"]
    assert skipped == {"Bare": "no careers_url or domain"}

    _, added, _ = merge(_TARGET, companies)
    assert added == ["Bare", "Domained", "Urled"]


def test_load_company_file_accepts_list_nested_under_one_key(tmp_path: Path) -> None:
    from jobforce.cli.config_lookup import _load_company_file

    f = tmp_path / "events.yaml"
    f.write_text('event_companies:\n  - name: "Acme"\n    domain: "acme.com"\n    events: 3\n')

    assert _load_company_file(str(f)) == [{"name": "Acme", "domain": "acme.com", "careers_url": ""}]


def test_name_skipped_then_added_is_not_reported_as_skipped() -> None:
    _, added, skipped = merge(_TARGET, [_c("Mango"), _c("Mango", "mango.ai")], skip_name_only=True)

    assert added == ["Mango"]
    assert skipped == {}
