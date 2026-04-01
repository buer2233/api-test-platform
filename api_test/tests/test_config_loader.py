import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_config_loader_module():
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
    module = _load_config_loader_module()
    module.clear_api_config_cache()

    config = module.get_api_config()

    assert config.runtime.base_url == "https://jsonplaceholder.typicode.com"
    assert config.runtime.timeout == 30
    assert config.execution.tests_root == "tests"
    assert config.execution.public_baseline_marker == "public_baseline"


def test_load_api_config_uses_explicit_path(tmp_path):
    module = _load_config_loader_module()
    custom_config = {
        "runtime": {
            "base_url": "https://example.com",
            "timeout": 15,
            "verify_ssl": True,
            "default_headers": {"Content-Type": "application/json"},
        },
        "session": {"pool_connections": 10, "pool_maxsize": 11, "max_retries": 2},
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


def test_load_api_config_rejects_missing_required_sections(tmp_path):
    module = _load_config_loader_module()
    config_path = tmp_path / "api_config.json"
    config_path.write_text(
        json.dumps({"runtime": {"base_url": "https://example.com"}}, ensure_ascii=False),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="session|execution|logging|site_profiles"):
        module.load_api_config(config_path)


def test_get_api_config_is_independent_from_current_workdir(monkeypatch):
    module = _load_config_loader_module()
    module.clear_api_config_cache()
    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    config = module.get_api_config()

    assert config.runtime.base_url == "https://jsonplaceholder.typicode.com"


def test_get_api_config_returns_cached_instance():
    module = _load_config_loader_module()
    module.clear_api_config_cache()

    first = module.get_api_config()
    second = module.get_api_config()

    assert first is second
