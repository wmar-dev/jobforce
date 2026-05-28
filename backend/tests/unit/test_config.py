from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from jobforce.config import load_config


def write_config(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content))
    return p


def test_valid_config_loads(tmp_path: Path) -> None:
    cfg_path = write_config(
        tmp_path,
        """
        search:
          queries:
            - query: "Python Engineer"
              location: "Remote"
        user:
          full_name: "Jane Smith"
          skills: ["Python"]
        """,
    )
    cfg = load_config(str(cfg_path))
    assert cfg.search.queries[0].query == "Python Engineer"
    assert cfg.user.skills == ["Python"]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="config.yaml not found"):
        load_config(str(tmp_path / "nonexistent.yaml"))


def test_missing_search_queries_raises(tmp_path: Path) -> None:
    cfg_path = write_config(
        tmp_path,
        """
        search:
          queries: []
        """,
    )
    with pytest.raises(Exception, match="search.queries"):
        load_config(str(cfg_path))


def test_extra_fields_ignored(tmp_path: Path) -> None:
    cfg_path = write_config(
        tmp_path,
        """
        unknown_top_level_key: "should be ignored"
        search:
          queries:
            - query: "Engineer"
        """,
    )
    cfg = load_config(str(cfg_path))
    assert cfg.search.queries[0].query == "Engineer"
