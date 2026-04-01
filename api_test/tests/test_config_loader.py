"""配置加载器治理测试。"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_config_loader_module():
    """按文件路径加载配置加载器模块，避免测试时受导入缓存干扰。"""
    module_path = Path(__file__).resolve().parents[1] / "core" / "config_loader.py"
    if not module_path.exists():
        raise ModuleNotFoundError("core.config_loader")
    spec = importlib.util.spec_from_file_location("config_loader_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_api_config_reads_default_json_file():
    """校验默认路径会读取唯一配置文件。"""
    module = _load_config_loader_module()
    module.clear_api_config_cache()

    config = module.get_api_config()

    assert config.runtime.base_url == "https://jsonplaceholder.typicode.com"
    assert config.runtime.timeout == 30
    assert config.proxy.enabled is False
    assert config.proxy.url == "http://127.0.0.1:7890"
    assert config.execution.tests_root == "tests"
    assert config.execution.public_baseline_marker == "public_baseline"


def test_load_api_config_uses_explicit_path(tmp_path):
    """校验显式路径参数会覆盖默认配置文件路径。"""
    module = _load_config_loader_module()
    custom_config = {
        "runtime": {
            "base_url": "https://example.com",
            "timeout": 15,
            "verify_ssl": True,
            "default_headers": {"Content-Type": "application/json"},
        },
        "session": {"pool_connections": 10, "pool_maxsize": 11, "max_retries": 2},
        "proxy": {"enabled": True, "url": "http://127.0.0.1:7891"},
        "execution": {
            "tests_root": "tests",
            "report_dir": "report",
            "default_pytest_args": ["-v"],
            "public_baseline_marker": "public_baseline",
        },
        "logging": {
            "enabled": False,
            "stack": False,
            "headers": False,
            "body": False,
            "response": False,
            "trace_id": True,
            "http_log_info": "logs/http_info.log",
            "http_log_conn": "logs/http_conn.log",
        },
        "site_profiles": {"jsonplaceholder": {"enabled": True, "supported_resources": ["posts"]}},
    }
    config_path = tmp_path / "api_config.json"
    config_path.write_text(json.dumps(custom_config, ensure_ascii=False, indent=2), encoding="utf-8")

    config = module.load_api_config(config_path)

    assert config.runtime.base_url == "https://example.com"
    assert config.session.pool_connections == 10
    assert config.proxy.enabled is True
    assert config.proxy.url == "http://127.0.0.1:7891"


def test_load_api_config_ignores_comment_fields(tmp_path):
    """校验加载器会忽略 JSON 配置中的中文说明字段。"""
    module = _load_config_loader_module()
    custom_config = {
        "_comment": "根配置说明",
        "runtime": {
            "_comment": "运行时说明",
            "base_url_comment": "地址说明",
            "base_url": "https://example.com",
            "timeout_comment": "超时说明",
            "timeout": 15,
            "verify_ssl_comment": "证书说明",
            "verify_ssl": True,
            "default_headers_comment": "请求头说明",
            "default_headers": {"Content-Type": "application/json"},
        },
        "session": {
            "_comment": "会话说明",
            "pool_connections_comment": "连接池说明",
            "pool_connections": 10,
            "pool_maxsize_comment": "最大连接数说明",
            "pool_maxsize": 11,
            "max_retries_comment": "重试说明",
            "max_retries": 2,
        },
        "proxy": {
            "_comment": "代理说明",
            "enabled_comment": "开关说明",
            "enabled": True,
            "url_comment": "地址说明",
            "url": "http://127.0.0.1:7891",
        },
        "execution": {
            "_comment": "执行说明",
            "tests_root_comment": "目录说明",
            "tests_root": "tests",
            "report_dir_comment": "报告说明",
            "report_dir": "report",
            "default_pytest_args_comment": "参数说明",
            "default_pytest_args": ["-v"],
            "public_baseline_marker_comment": "标记说明",
            "public_baseline_marker": "public_baseline",
        },
        "logging": {
            "_comment": "日志说明",
            "enabled_comment": "日志开关说明",
            "enabled": False,
            "stack_comment": "堆栈说明",
            "stack": False,
            "headers_comment": "请求头说明",
            "headers": False,
            "body_comment": "请求体说明",
            "body": False,
            "response_comment": "响应体说明",
            "response": False,
            "trace_id_comment": "trace_id 说明",
            "trace_id": True,
            "http_log_info_comment": "普通日志说明",
            "http_log_info": "logs/http_info.log",
            "http_log_conn_comment": "连接日志说明",
            "http_log_conn": "logs/http_conn.log",
        },
        "site_profiles": {
            "_comment": "站点说明",
            "jsonplaceholder_comment": "公开站点说明",
            "jsonplaceholder": {"enabled": True, "supported_resources": ["posts"]},
        },
    }
    config_path = tmp_path / "api_config.json"
    config_path.write_text(json.dumps(custom_config, ensure_ascii=False, indent=2), encoding="utf-8")

    config = module.load_api_config(config_path)

    assert config.runtime.base_url == "https://example.com"
    assert config.site_profiles["jsonplaceholder"].enabled is True
    assert config.site_profiles["jsonplaceholder"].supported_resources == ["posts"]


def test_load_api_config_rejects_missing_required_sections(tmp_path):
    """校验缺少必要配置分组时会报错。"""
    module = _load_config_loader_module()
    config_path = tmp_path / "api_config.json"
    config_path.write_text(
        json.dumps({"runtime": {"base_url": "https://example.com"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="session|proxy|execution|logging|site_profiles"):
        module.load_api_config(config_path)


def test_get_api_config_is_independent_from_current_workdir(monkeypatch):
    """校验切换工作目录后仍可定位到默认配置文件。"""
    module = _load_config_loader_module()
    module.clear_api_config_cache()
    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    config = module.get_api_config()

    assert config.runtime.base_url == "https://jsonplaceholder.typicode.com"


def test_get_api_config_returns_cached_instance():
    """校验配置加载结果会被缓存复用。"""
    module = _load_config_loader_module()
    module.clear_api_config_cache()

    first = module.get_api_config()
    second = module.get_api_config()

    assert first is second
