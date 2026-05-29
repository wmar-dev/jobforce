from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

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


def test_company_config_careers_url(tmp_path: Path) -> None:
    cfg_path = write_config(
        tmp_path,
        """
        search:
          queries:
            - query: "Engineer"
          target_companies:
            - name: "Acme Corp"
              domain: "acme.com"
              careers_url: "https://boards.greenhouse.io/acme"
            - name: "No URL Corp"
              domain: "nourls.com"
        """,
    )
    cfg = load_config(str(cfg_path))
    acme = cfg.search.target_companies[0]
    assert acme.name == "Acme Corp"
    assert acme.careers_url == "https://boards.greenhouse.io/acme"
    no_url = cfg.search.target_companies[1]
    assert no_url.careers_url == ""


def test_jobforce_db_path_env_overrides_config(tmp_path: Path) -> None:
    cfg_path = write_config(
        tmp_path,
        """
        search:
          queries:
            - query: "Engineer"
        database:
          path: "backend/data/jobforce.db"
        """,
    )
    with patch.dict("os.environ", {"JOBFORCE_DB_PATH": "/tmp/test.db"}):
        cfg = load_config(str(cfg_path))
    assert cfg.database.path == "/tmp/test.db"


def test_jobforce_db_path_dotenv_overrides_config(tmp_path: Path) -> None:
    cfg_path = write_config(
        tmp_path,
        """
        search:
          queries:
            - query: "Engineer"
        database:
          path: "backend/data/jobforce.db"
        """,
    )
    env_file = tmp_path / ".env"
    env_file.write_text("JOBFORCE_DB_PATH=/tmp/dotenv.db\n")
    # Temporarily make _load_env_settings find our .env by patching Path.cwd
    with patch("jobforce.config.Path.cwd", return_value=tmp_path):
        cfg = load_config(str(cfg_path))
    assert cfg.database.path == "/tmp/dotenv.db"
