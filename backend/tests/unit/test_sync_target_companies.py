"""Unit tests for jobforce.cli.sync_target_companies."""

from __future__ import annotations

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
    assert skipped == ["Ask HN: Who Is Hiring?", "Sequoia Companies"]


def test_duplicate_config_entries_prefer_one_with_careers_url() -> None:
    text, added, _ = merge(_TARGET, [_c("Mango"), _c("Mango", careers_url="https://mango.ai/jobs")])

    assert added == ["Mango"]
    mango = [e for e in yaml.safe_load(text) if e["name"] == "Mango"]
    assert mango == [{"name": "Mango", "domain": "", "careers_url": "https://mango.ai/jobs"}]


def test_domain_url_is_normalized_and_quotes_escaped() -> None:
    text, _, _ = merge(_TARGET, [_c('Say "Hi"', "https://www.sayhi.ai/")])

    entry = [e for e in yaml.safe_load(text) if e["name"] == 'Say "Hi"'][0]
    assert entry["domain"] == "sayhi.ai"
