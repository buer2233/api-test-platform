"""`api_test` 唯一配置源加载器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    """运行时基础配置模型。"""

    base_url: str
    timeout: int
    verify_ssl: bool
    default_headers: dict[str, str] = Field(default_factory=dict)


class SessionConfig(BaseModel):
    """会话层连接池和重试配置模型。"""

    pool_connections: int
    pool_maxsize: int
    max_retries: int


class ProxyConfig(BaseModel):
    """代理配置模型。"""

    enabled: bool = False
    url: str = "http://127.0.0.1:7890"


class ExecutionConfig(BaseModel):
    """执行入口配置模型。"""

    tests_root: str
    report_dir: str
    default_pytest_args: list[str] = Field(default_factory=list)
    public_baseline_marker: str


class LoggingConfig(BaseModel):
    """日志输出配置模型。"""

    enabled: bool
    stack: bool
    headers: bool
    body: bool
    response: bool
    trace_id: bool
    http_log_info: str
    http_log_conn: str


class SiteProfile(BaseModel):
    """公开测试站点能力配置模型。"""

    enabled: bool
    supported_resources: list[str] = Field(default_factory=list)


class ApiTestConfig(BaseModel):
    """`api_test` 顶层配置模型。"""

    runtime: RuntimeConfig
    session: SessionConfig
    proxy: ProxyConfig
    execution: ExecutionConfig
    logging: LoggingConfig
    site_profiles: dict[str, SiteProfile] = Field(default_factory=dict)


_CONFIG_CACHE: ApiTestConfig | None = None


def _strip_comment_fields(value: Any) -> Any:
    """递归移除 `_comment` 和 `*_comment` 说明字段，避免影响配置校验。"""
    if isinstance(value, dict):
        return {
            key: _strip_comment_fields(item)
            for key, item in value.items()
            if key != "_comment" and not key.endswith("_comment")
        }
    if isinstance(value, list):
        return [_strip_comment_fields(item) for item in value]
    return value


def get_api_test_root() -> Path:
    """返回 `api_test` 根目录路径。"""
    return Path(__file__).resolve().parents[1]


def get_default_config_path() -> Path:
    """返回默认配置文件 `api_config.json` 的绝对路径。"""
    return get_api_test_root() / "api_config.json"


def load_api_config(config_path: str | Path | None = None) -> ApiTestConfig:
    """读取并校验配置文件。

    参数说明：
    - `config_path`：可选配置文件路径；不传时默认读取 `api_config.json`。
    """
    path = Path(config_path) if config_path else get_default_config_path()
    payload: dict[str, Any] = _strip_comment_fields(json.loads(path.read_text(encoding="utf-8")))
    missing_sections = [
        section
        for section in ("runtime", "session", "proxy", "execution", "logging", "site_profiles")
        if section not in payload
    ]
    if missing_sections:
        raise ValueError(f"配置缺少必要分组: {', '.join(missing_sections)}")
    return ApiTestConfig.model_validate(payload)


def get_api_config() -> ApiTestConfig:
    """返回缓存后的配置对象，避免重复解析 JSON。"""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_api_config()
    return _CONFIG_CACHE


def clear_api_config_cache() -> None:
    """清空配置缓存，供测试或配置切换场景重新加载。"""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None
