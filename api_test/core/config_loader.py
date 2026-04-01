from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    base_url: str
    timeout: int
    verify_ssl: bool
    default_headers: dict[str, str] = Field(default_factory=dict)


class SessionConfig(BaseModel):
    pool_connections: int
    pool_maxsize: int
    max_retries: int


class ExecutionConfig(BaseModel):
    tests_root: str
    report_dir: str
    default_pytest_args: list[str] = Field(default_factory=list)
    public_baseline_marker: str


class LoggingConfig(BaseModel):
    enabled: bool
    stack: bool
    headers: bool
    body: bool
    response: bool
    trace_id: bool
    http_log_info: str
    http_log_conn: str


class SiteProfile(BaseModel):
    enabled: bool
    supported_resources: list[str] = Field(default_factory=list)


class ApiTestConfig(BaseModel):
    runtime: RuntimeConfig
    session: SessionConfig
    execution: ExecutionConfig
    logging: LoggingConfig
    site_profiles: dict[str, SiteProfile] = Field(default_factory=dict)


_CONFIG_CACHE: ApiTestConfig | None = None


def get_api_test_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_default_config_path() -> Path:
    return get_api_test_root() / "api_config.json"


def load_api_config(config_path: str | Path | None = None) -> ApiTestConfig:
    path = Path(config_path) if config_path else get_default_config_path()
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    missing_sections = [
        section
        for section in ("runtime", "session", "execution", "logging", "site_profiles")
        if section not in payload
    ]
    if missing_sections:
        raise ValueError(f"配置缺少必要分组: {', '.join(missing_sections)}")
    return ApiTestConfig.model_validate(payload)


def get_api_config() -> ApiTestConfig:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_api_config()
    return _CONFIG_CACHE


def clear_api_config_cache() -> None:
    global _CONFIG_CACHE
    _CONFIG_CACHE = None
