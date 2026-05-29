from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator


class DatabaseConfig(BaseModel):
    path: str = "backend/data/jobforce.db"


class SearchQueryConfig(BaseModel):
    query: str
    location: str = ""
    source: str = "linkedin"


class CompanyConfig(BaseModel):
    name: str
    domain: str = ""
    careers_url: str = ""


class UserConfig(BaseModel):
    full_name: str = ""
    headline: str = ""
    skills: list[str] = []
    preferences: dict[str, Any] = {}


class SearchConfig(BaseModel):
    queries: list[SearchQueryConfig] = []
    target_companies: list[CompanyConfig] = []

    @field_validator("queries", mode="before")
    @classmethod
    def require_at_least_one_query(cls, v: Any) -> Any:
        if isinstance(v, list) and len(v) == 0:
            raise ValueError(
                "config.yaml: search.queries is required and must have at least one entry"
            )
        return v


class AppConfig(BaseModel):
    model_config = {"extra": "ignore"}

    database: DatabaseConfig = DatabaseConfig()
    search: SearchConfig = SearchConfig()
    user: UserConfig = UserConfig()


def _find_config(path: str) -> Path:
    config_path = Path(path)
    if config_path.is_absolute():
        return config_path
    # Search from CWD, then walk up to project root (where config.example.yaml lives)
    candidate = Path.cwd() / config_path
    if candidate.exists():
        return candidate
    # Walk up from this file's location (backend/jobforce/) to find repo root
    here = Path(__file__).parent
    for parent in [here, here.parent, here.parent.parent]:
        candidate = parent / config_path
        if candidate.exists():
            return candidate
    return Path.cwd() / config_path  # let it fail with a clear message below


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = _find_config(path)
    if not config_path.exists():
        raise FileNotFoundError(
            "config.yaml not found. Searched CWD and parent directories. "
            "Copy config.example.yaml to config.yaml and fill in your details."
        )
    with config_path.open() as f:
        raw = yaml.safe_load(f) or {}
    return AppConfig.model_validate(raw)


_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config
