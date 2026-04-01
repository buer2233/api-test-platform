# Generic Test Framework Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `api_test/` into a configuration-driven generic HTTP test framework, remove legacy private-site logic, de-specialize `platform_core/`, and keep the V1 document-driven platform pipeline passing.

**Architecture:** The refactor splits the work into three vertical tracks: `api_test` configuration foundation, `api_test` runtime and execution cleanup, and `platform_core` removal of the old `PublicAPI` bridge. The implementation stays TDD-first, deletes private-site pathways instead of wrapping them, and updates every affected product and phase document in the same round.

**Tech Stack:** Python 3.12, pytest, requests, pydantic, Jinja2, Markdown, Git

---

## File Map

### Create
- `api_test/api_config.json`
- `api_test/core/config_loader.py`
- `api_test/tests/test_config_loader.py`

### Modify
- `api_test/core/base_api.py`
- `api_test/core/session.py`
- `api_test/core/jsonplaceholder_api.py`
- `api_test/core/__init__.py`
- `api_test/conftest.py`
- `api_test/run_test.py`
- `api_test/pytest.ini`
- `api_test/tests/test_base_api_governance.py`
- `api_test/tests/test_jsonplaceholder_api.py`
- `api_test/tests/test_jsonplaceholder_resources.py`
- `api_test/tests/test_run_test.py`
- `platform_core/cli.py`
- `platform_core/services.py`
- `platform_core/rules.py`
- `tests/platform_core/test_services_and_assets.py`
- `tests/platform_core/test_templates_and_rules.py`
- `README.md`
- `api_test/README.md`
- `api_test/QUICKSTART.md`
- `product_document/架构设计/总体架构设计说明书.md`
- `product_document/架构设计/现有接口自动化测试框架改造方案.md`
- `product_document/架构设计/中间模型设计说明书.md`
- `product_document/架构设计/模板体系与代码生成规范说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

### Delete
- `api_test/config.py`
- `api_test/core/private_env.py`
- `api_test/core/public_api.py`
- `api_test/legacy_api_catalog.py`
- `api_test/core/legacy_assets.py`
- `api_test/tests/test_demo.py`
- `api_test/tests/test_public_api_governance.py`
- `api_test/test_data/account.txt`
- `platform_core/legacy_assets.py`

---

### Task 1: Build The JSON Configuration Foundation

**Files:**
- Create: `api_test/api_config.json`
- Create: `api_test/core/config_loader.py`
- Test: `api_test/tests/test_config_loader.py`

- [ ] **Step 1: Write the failing configuration tests**

```python
# api_test/tests/test_config_loader.py
import json
from pathlib import Path

import pytest

from core.config_loader import clear_api_config_cache, get_api_config, load_api_config


def test_load_api_config_reads_default_json_file():
    clear_api_config_cache()
    config = get_api_config()
    assert config.runtime.base_url == "https://jsonplaceholder.typicode.com"
    assert config.runtime.timeout == 30
    assert config.execution.tests_root == "tests"
    assert config.execution.public_baseline_marker == "public_baseline"


def test_load_api_config_uses_explicit_path(tmp_path):
    custom_config = {
        "runtime": {
            "base_url": "https://example.com",
            "timeout": 15,
            "verify_ssl": True,
            "default_headers": {"Content-Type": "application/json"}
        },
        "session": {"pool_connections": 10, "pool_maxsize": 11, "max_retries": 2},
        "execution": {
            "tests_root": "tests",
            "report_dir": "report",
            "default_pytest_args": ["-v"],
            "public_baseline_marker": "public_baseline"
        },
        "logging": {
            "enabled": False,
            "stack": False,
            "headers": False,
            "body": False,
            "response": False,
            "trace_id": True,
            "http_log_info": "logs/http_info.log",
            "http_log_conn": "logs/http_conn.log"
        },
        "site_profiles": {"jsonplaceholder": {"enabled": True, "supported_resources": ["posts"]}}
    }
    config_path = tmp_path / "api_config.json"
    config_path.write_text(json.dumps(custom_config, ensure_ascii=False, indent=2), encoding="utf-8")

    config = load_api_config(config_path)

    assert config.runtime.base_url == "https://example.com"
    assert config.session.pool_connections == 10


def test_load_api_config_rejects_missing_required_sections(tmp_path):
    config_path = tmp_path / "api_config.json"
    config_path.write_text(json.dumps({"runtime": {"base_url": "https://example.com"}}, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="session|execution|logging|site_profiles"):
        load_api_config(config_path)


def test_get_api_config_is_independent_from_current_workdir(monkeypatch):
    clear_api_config_cache()
    monkeypatch.chdir(Path(__file__).resolve().parents[2])

    config = get_api_config()

    assert config.runtime.base_url == "https://jsonplaceholder.typicode.com"


def test_get_api_config_returns_cached_instance():
    clear_api_config_cache()
    first = get_api_config()
    second = get_api_config()
    assert first is second
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest api_test/tests/test_config_loader.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'core.config_loader'`.

- [ ] **Step 3: Write the minimal configuration implementation**

```json
// api_test/api_config.json
{
  "runtime": {
    "base_url": "https://jsonplaceholder.typicode.com",
    "timeout": 30,
    "verify_ssl": true,
    "default_headers": {
      "Content-Type": "application/json"
    }
  },
  "session": {
    "pool_connections": 100,
    "pool_maxsize": 100,
    "max_retries": 3
  },
  "execution": {
    "tests_root": "tests",
    "report_dir": "report",
    "default_pytest_args": [
      "-v",
      "--strict-markers",
      "--tb=short",
      "--disable-warnings"
    ],
    "public_baseline_marker": "public_baseline"
  },
  "logging": {
    "enabled": false,
    "stack": false,
    "headers": false,
    "body": false,
    "response": false,
    "trace_id": true,
    "http_log_info": "logs/http_info.log",
    "http_log_conn": "logs/http_conn.log"
  },
  "site_profiles": {
    "jsonplaceholder": {
      "enabled": true,
      "supported_resources": [
        "posts",
        "comments",
        "albums",
        "photos",
        "todos",
        "users"
      ]
    }
  }
}
```

```python
# api_test/core/config_loader.py
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
    missing_sections = [name for name in ("runtime", "session", "execution", "logging", "site_profiles") if name not in payload]
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
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest api_test/tests/test_config_loader.py -v
```

Expected: PASS with `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add api_test/api_config.json api_test/core/config_loader.py api_test/tests/test_config_loader.py
git commit -m "重构：建立 api_config.json 唯一配置源与配置加载器"
```

---

### Task 2: Refactor Session And BaseAPI Into Generic Runtime Components

**Files:**
- Modify: `api_test/core/session.py`
- Modify: `api_test/core/base_api.py`
- Test: `api_test/tests/test_base_api_governance.py`

- [ ] **Step 1: Write the failing runtime-governance test**

```python
# api_test/tests/test_base_api_governance.py
import pytest
import requests

from core.base_api import BaseAPI
from core.config_loader import clear_api_config_cache, get_api_config
from core.session import build_retry_session


def test_build_retry_session_uses_config_values():
    config = get_api_config()
    session = build_retry_session()
    assert isinstance(session.adapters["http://"], requests.adapters.HTTPAdapter)
    assert isinstance(session.adapters["https://"], requests.adapters.HTTPAdapter)
    assert session.adapters["http://"]._pool_connections == config.session.pool_connections
    assert session.adapters["https://"]._pool_maxsize == config.session.pool_maxsize
    session.close()


def test_base_api_uses_json_runtime_config():
    clear_api_config_cache()
    api = BaseAPI()
    assert api.base_url == "https://jsonplaceholder.typicode.com"
    assert api.timeout == 30
    assert api.verify_ssl is True
    assert api.default_headers["Content-Type"] == "application/json"
    api.session.close()


def test_request_returns_raw_response_when_notjson(monkeypatch):
    class DummyResponse:
        status_code = 200
        text = "ok"

        @staticmethod
        def json():
            return {"status": True}

    api = BaseAPI()
    monkeypatch.setattr(api.session, "request", lambda **kwargs: DummyResponse())
    response = api.post("/api/demo", NOTJSON=True)
    assert response.status_code == 200
    assert response.text == "ok"
    api.session.close()


def test_request_accepts_expected_status_override(monkeypatch):
    class DummyResponse:
        status_code = 201
        text = '{"id": 101}'

        @staticmethod
        def json():
            return {"id": 101}

    api = BaseAPI()
    monkeypatch.setattr(api.session, "request", lambda **kwargs: DummyResponse())
    response = api.post("/posts", expected_status=201)
    assert response["id"] == 101
    api.session.close()


def test_request_rejects_unexpected_status(monkeypatch):
    class DummyResponse:
        status_code = 202
        text = "accepted"

        @staticmethod
        def json():
            return {"status": "accepted"}

    api = BaseAPI()
    monkeypatch.setattr(api.session, "request", lambda **kwargs: DummyResponse())
    with pytest.raises(AssertionError, match="状态码"):
        api.post("/posts", expected_status=(200, 201))
    api.session.close()


def test_put_helper_delegates_to_request(monkeypatch):
    api = BaseAPI()
    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)

        class DummyResponse:
            status_code = 200
            text = '{"ok": true}'

            @staticmethod
            def json():
                return {"ok": True}

        return DummyResponse()

    monkeypatch.setattr(api.session, "request", fake_request)
    response = api.put("/posts/1", json={"title": "updated"})
    assert captured["method"] == "PUT"
    assert captured["json"] == {"title": "updated"}
    assert response["ok"] is True
    api.session.close()


def test_patch_helper_delegates_to_request(monkeypatch):
    api = BaseAPI()
    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)

        class DummyResponse:
            status_code = 200
            text = '{"ok": true}'

            @staticmethod
            def json():
                return {"ok": True}

        return DummyResponse()

    monkeypatch.setattr(api.session, "request", fake_request)
    response = api.patch("/posts/1", json={"title": "patched"})
    assert captured["method"] == "PATCH"
    assert captured["json"] == {"title": "patched"}
    assert response["ok"] is True
    api.session.close()


def test_base_api_no_longer_exposes_private_login_helpers():
    assert not hasattr(BaseAPI, "password_rsa")
    assert not hasattr(BaseAPI, "login")
    assert not hasattr(BaseAPI, "get_admin_session")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest api_test/tests/test_base_api_governance.py -v
```

Expected: FAIL with import or attribute errors because `BaseAPI` still depends on deleted private-site logic.

- [ ] **Step 3: Write the minimal generic runtime implementation**

```python
# api_test/core/session.py
"""HTTP Session builder for the generic test runtime."""

from __future__ import annotations

import requests

from core.config_loader import get_api_config


def build_retry_session(
    pool_connections: int | None = None,
    pool_maxsize: int | None = None,
    max_retries: int | None = None,
) -> requests.Session:
    config = get_api_config().session
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=pool_connections if pool_connections is not None else config.pool_connections,
        pool_maxsize=pool_maxsize if pool_maxsize is not None else config.pool_maxsize,
        max_retries=max_retries if max_retries is not None else config.max_retries,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

```python
# api_test/core/base_api.py
"""Generic HTTP API base client for public and internal site adapters."""

from __future__ import annotations

import base64
import hashlib
import random
import string
import time
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any

from core.config_loader import get_api_config
from core.session import build_retry_session


class BaseAPI:
    """Generic HTTP API client with shared utility helpers."""

    def __init__(self) -> None:
        config = get_api_config()
        self.base_url = config.runtime.base_url.rstrip("/")
        self.timeout = config.runtime.timeout
        self.verify_ssl = config.runtime.verify_ssl
        self.default_headers = dict(config.runtime.default_headers)
        self.session = build_retry_session()

    def request(self, method: str, url: str, expected_status: int | Iterable[int] = 200, **kwargs: Any) -> Any:
        not_json = bool(kwargs.pop("NOTJSON", False))
        allowed_statuses = self._normalize_expected_status(expected_status)
        headers = dict(self.default_headers)
        headers.update(kwargs.pop("headers", {}))
        final_url = url if url.startswith(("http://", "https://")) else f"{self.base_url}{url}"
        response = self.session.request(
            method=method.upper(),
            url=final_url,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify_ssl,
            **kwargs,
        )
        assert response.status_code in allowed_statuses, (
            f"请求失败: {method} {final_url}\n"
            f"状态码: {response.status_code}, 期望: {allowed_statuses}\n"
            f"响应: {response.text}"
        )
        return response if not_json else response.json()

    @staticmethod
    def _normalize_expected_status(expected_status: int | Iterable[int]) -> tuple[int, ...]:
        if isinstance(expected_status, int):
            return (expected_status,)
        normalized = tuple(expected_status)
        assert normalized, "expected_status 不能为空"
        return normalized

    def get(self, url: str, **kwargs: Any) -> Any:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Any:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Any:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Any:
        return self.request("DELETE", url, **kwargs)

    @staticmethod
    def get_value(data: Any, keys: list[str] | str, msg: str = "") -> Any:
        path = keys if isinstance(keys, list) else [keys]
        try:
            for key in path:
                data = data[key]
            return data
        except (KeyError, IndexError, TypeError) as exc:
            error_msg = f"数据中不存在路径 '{path}'"
            if msg:
                error_msg = f"{msg}: {error_msg}"
            raise AssertionError(error_msg) from exc

    @staticmethod
    def time_to_stamp(date_str: str, is_all_day: bool = False) -> str:
        fmt = "%Y-%m-%d" if is_all_day else "%Y-%m-%d %H:%M:%S"
        return str(int(time.mktime(time.strptime(date_str, fmt)) * 1000))

    @staticmethod
    def stamp_to_time(timestamp: int) -> str:
        if len(str(timestamp)) == 13:
            timestamp = int(timestamp / 1000)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    @staticmethod
    def get_week_info(day: date | str | None = None) -> tuple[str, str]:
        if day is None:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, "%Y-%m-%d").date()
        monday = day - timedelta(days=day.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    @staticmethod
    def get_month_info(day: date | str | None = None) -> tuple[str, str, int]:
        if day is None:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, "%Y-%m-%d").date()
        first_day = date(day.year, day.month, 1)
        next_month = date(day.year + 1, 1, 1) if day.month == 12 else date(day.year, day.month + 1, 1)
        last_day = next_month - timedelta(days=1)
        total_days = (last_day - first_day).days + 1
        return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"), total_days

    @staticmethod
    def md5_encrypt(text: str) -> str:
        digest = hashlib.md5()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest().lower()

    @staticmethod
    def sha1_encrypt(text: str) -> str:
        digest = hashlib.sha1()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def aes_ecb_encrypt(plain_text: str, key: str) -> str:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def aes_ecb_decrypt(cipher_text: str, key: str) -> str:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        decrypted = cipher.decrypt(base64.b64decode(cipher_text))
        return unpad(decrypted, AES.block_size).decode("utf-8")

    @staticmethod
    def aes_cbc_encrypt(plain_text: str, key: str, iv: str) -> str:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def aes_cbc_decrypt(cipher_text: str, key: str, iv: str) -> str:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        decrypted = cipher.decrypt(base64.b64decode(cipher_text))
        return unpad(decrypted, AES.block_size).decode("utf-8")

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        return "".join(random.sample(string.ascii_lowercase + string.digits, length))

    @staticmethod
    def generate_phone_number() -> str:
        second = random.choice([3, 4, 5, 7, 8])
        third = random.choice(list("0123456789"))
        return f"1{second}{third}{random.randint(10000000, 99999999)}"

    @staticmethod
    def generate_email(prefix: str | None = None) -> str:
        prefix = prefix or BaseAPI.generate_random_string(8)
        return f"{prefix}{int(time.time() * 1000)}@etest.com"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest api_test/tests/test_base_api_governance.py -v
```

Expected: PASS with `8 passed`.

- [ ] **Step 5: Commit**

```bash
git add api_test/core/session.py api_test/core/base_api.py api_test/tests/test_base_api_governance.py
git commit -m "重构：将 BaseAPI 与 Session 收口为通用运行时底座"
```

---

### Task 3: Convert Fixtures And Site Tests To Public Generic Baseline

**Files:**
- Modify: `api_test/conftest.py`
- Modify: `api_test/core/jsonplaceholder_api.py`
- Modify: `api_test/pytest.ini`
- Test: `api_test/tests/test_jsonplaceholder_api.py`
- Test: `api_test/tests/test_jsonplaceholder_resources.py`

- [ ] **Step 1: Write the failing public-baseline tests**

```python
# api_test/tests/test_jsonplaceholder_resources.py
import pytest


pytestmark = [pytest.mark.jsonplaceholder, pytest.mark.public_baseline]


def test_jsonplaceholder_fixture_uses_public_base_url(jsonplaceholder_api):
    assert jsonplaceholder_api.base_url == "https://jsonplaceholder.typicode.com"


def test_get_user_resource_contract(jsonplaceholder_api):
    payload = jsonplaceholder_api.get_user(1)
    assert payload["id"] == 1
    assert "username" in payload


def test_list_users_returns_stable_collection_shape(jsonplaceholder_api):
    payload = jsonplaceholder_api.list_users()
    assert isinstance(payload, list)
    assert len(payload) == 10
    assert "email" in payload[0]


def test_list_todos_by_user_id_filters_collection(jsonplaceholder_api):
    payload = jsonplaceholder_api.list_todos(userId=1)
    assert payload
    assert all(item["userId"] == 1 for item in payload)


def test_list_user_todos_supports_nested_route(jsonplaceholder_api):
    payload = jsonplaceholder_api.list_user_todos(1)
    assert payload
    assert all(item["userId"] == 1 for item in payload)
```

```python
# api_test/tests/test_jsonplaceholder_api.py
import pytest


pytestmark = [pytest.mark.jsonplaceholder, pytest.mark.public_baseline]


class TestJsonPlaceholderAPI:
    def test_get_single_post(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.get_post(1)
        assert payload["id"] == 1

    def test_filter_posts_by_user_id(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.list_posts(userId=1)
        assert payload
        assert all(item["userId"] == 1 for item in payload)

    def test_nested_comments_route(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.list_post_comments(1)
        assert payload
        assert all(item["postId"] == 1 for item in payload)

    def test_create_post_uses_fake_write_contract(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.create_post(title="demo", body="payload", user_id=1)
        assert payload["title"] == "demo"
        assert payload["id"] == 101

    def test_put_replaces_post_payload(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.replace_post(1, title="new", body="body", user_id=1)
        assert payload["id"] == 1
        assert payload["title"] == "new"

    def test_patch_updates_partial_fields(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.patch_post(1, title="patched")
        assert payload["title"] == "patched"

    def test_delete_returns_empty_object(self, jsonplaceholder_api):
        payload = jsonplaceholder_api.delete_post(1)
        assert payload == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest api_test/tests/test_jsonplaceholder_api.py api_test/tests/test_jsonplaceholder_resources.py -v
```

Expected: FAIL because fixture and markers still depend on old config/conftest assumptions.

- [ ] **Step 3: Write the minimal fixture and adapter implementation**

```python
# api_test/conftest.py
"""Shared pytest fixtures and report hooks for the generic api_test suite."""

from __future__ import annotations

from datetime import datetime

import pytest
from py.xml import html

from core.config_loader import get_api_config
from core.jsonplaceholder_api import JsonPlaceholderAPI


@pytest.fixture(scope="function")
def base_url() -> str:
    return get_api_config().runtime.base_url


@pytest.fixture(scope="function")
def jsonplaceholder_api():
    api = JsonPlaceholderAPI()
    yield api
    api.session.close()


@pytest.fixture(autouse=True)
def test_description(request):
    description = getattr(getattr(request.node, "_obj", None), "__doc__", None) or "未提供用例描述"
    request.node._description = description
    yield


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([html.p(f"测试环境: {get_api_config().runtime.base_url}")])
    prefix.extend([html.p(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")])


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(1, html.th("描述"))
    cells.insert(2, html.th("用例ID"))
    cells.insert(3, html.th("状态"))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    description = getattr(report, "description", "") or str(report.nodeid)
    cells.insert(1, html.td(description))
    cells.insert(2, html.td(report.nodeid))
    status = '<span style="color:green">通过</span>' if report.passed else '<span style="color:red">失败</span>' if report.failed else '<span style="color:orange">跳过</span>'
    cells.insert(3, html.td(status))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.description = getattr(item, "_description", "未提供用例描述")


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_html(report, data):
    if report.passed:
        data[:] = [html.div("测试通过，无详细日志", class_="empty log")]
```

```ini
# api_test/pytest.ini
[pytest]
disable_test_id_escaping_and_forfeit_all_rights_to_community_support = True
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
asyncio_default_fixture_loop_scope = function
markers =
    jsonplaceholder: 基于 JSONPlaceholder 公共测试站点的公开接口用例
    public_baseline: 当前公开回归基线用例
    unit: 单元测试
    integration: 集成测试
    regression: 回归测试
    smoke: 冒烟测试
    P0: P0级用例
```

```python
# api_test/core/jsonplaceholder_api.py
"""JSONPlaceholder public-site adapter used as the default public baseline."""

from __future__ import annotations

from typing import Any

from core.base_api import BaseAPI


class JsonPlaceholderAPI(BaseAPI):
    def list_posts(self, **params) -> list[dict[str, Any]]:
        return self.get("/posts", params=params)

    def get_post(self, post_id: int) -> dict[str, Any]:
        return self.get(f"/posts/{post_id}")

    def list_post_comments(self, post_id: int) -> list[dict[str, Any]]:
        return self.get(f"/posts/{post_id}/comments")

    def list_user_posts(self, user_id: int) -> list[dict[str, Any]]:
        return self.get("/posts", params={"userId": user_id})

    def list_users(self) -> list[dict[str, Any]]:
        return self.get("/users")

    def get_user(self, user_id: int) -> dict[str, Any]:
        return self.get(f"/users/{user_id}")

    def list_todos(self, **params) -> list[dict[str, Any]]:
        return self.get("/todos", params=params)

    def list_user_todos(self, user_id: int) -> list[dict[str, Any]]:
        return self.get(f"/users/{user_id}/todos")

    def create_post(self, title: str, body: str, user_id: int) -> dict[str, Any]:
        return self.post("/posts", json={"title": title, "body": body, "userId": user_id}, expected_status=201)

    def replace_post(self, post_id: int, title: str, body: str, user_id: int) -> dict[str, Any]:
        return self.put(f"/posts/{post_id}", json={"id": post_id, "title": title, "body": body, "userId": user_id})

    def patch_post(self, post_id: int, **fields: Any) -> dict[str, Any]:
        return self.patch(f"/posts/{post_id}", json=fields)

    def delete_post(self, post_id: int) -> dict[str, Any]:
        return self.delete(f"/posts/{post_id}")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest api_test/tests/test_jsonplaceholder_api.py api_test/tests/test_jsonplaceholder_resources.py -v
```

Expected: PASS with `12 passed`.

- [ ] **Step 5: Commit**

```bash
git add api_test/conftest.py api_test/core/jsonplaceholder_api.py api_test/pytest.ini api_test/tests/test_jsonplaceholder_api.py api_test/tests/test_jsonplaceholder_resources.py
git commit -m "重构：将公开基线统一为通用 public_baseline 标记"
```

---

### Task 4: Make `run_test.py` Work From Any Working Directory

**Files:**
- Modify: `api_test/run_test.py`
- Test: `api_test/tests/test_run_test.py`

- [ ] **Step 1: Write the failing run-script tests**

```python
# api_test/tests/test_run_test.py
from argparse import Namespace
from pathlib import Path

import run_test


def test_build_pytest_command_supports_public_baseline_filter():
    args = Namespace(mark=None, file=None, html=False, reruns=0, verbose=False, public_baseline=True)

    command = run_test.build_pytest_command(args)

    assert command[:5] == [
        "pytest",
        "-v",
        "-c",
        str(run_test.get_pytest_config_path()),
        str(run_test.get_tests_root()),
    ]
    assert command[5:7] == ["-m", "public_baseline"]


def test_build_pytest_command_combines_marker_with_public_baseline():
    args = Namespace(mark="jsonplaceholder", file="tests/test_jsonplaceholder_api.py", html=True, reruns=2, verbose=True, public_baseline=True)

    command = run_test.build_pytest_command(args)

    assert command[:2] == ["pytest", "-vv"]
    assert command[2:6] == ["-c", str(run_test.get_pytest_config_path()), str(run_test.get_tests_root()), "-m"]
    assert command[6] == "(jsonplaceholder) and public_baseline"
    assert str(Path("tests/test_jsonplaceholder_api.py")) in command
    assert "--html" in command
    assert "--reruns" in command
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest api_test/tests/test_run_test.py -v
```

Expected: FAIL because command still uses `not private_env` and cwd-dependent paths.

- [ ] **Step 3: Write the minimal execution-entry implementation**

```python
# api_test/run_test.py
"""Stable pytest launcher for the generic api_test suite."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from core.config_loader import get_api_config


def get_api_test_root() -> Path:
    return Path(__file__).resolve().parent


def get_tests_root() -> Path:
    return get_api_test_root() / get_api_config().execution.tests_root


def get_pytest_config_path() -> Path:
    return get_api_test_root() / "pytest.ini"


def build_pytest_command(args) -> list[str]:
    config = get_api_config()
    cmd = ["pytest", "-vv" if args.verbose else "-v", "-c", str(get_pytest_config_path()), str(get_tests_root())]
    marker_expression = args.mark
    if args.public_baseline:
        public_expression = config.execution.public_baseline_marker
        marker_expression = f"({marker_expression}) and {public_expression}" if marker_expression else public_expression
    if marker_expression:
        cmd.extend(["-m", marker_expression])
    if args.file:
        cmd.append(str(Path(args.file)))
    if args.html:
        report_dir = get_api_test_root() / config.execution.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--html", str(report_dir / "report.html"), "--self-contained-html"])
    if args.reruns:
        cmd.extend(["--reruns", str(args.reruns)])
    return cmd


def run_pytest(args) -> int:
    cmd = build_pytest_command(args)
    print(f"执行命令: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=get_api_test_root()).returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="接口自动化测试运行器")
    parser.add_argument("-m", "--mark", help="按标记运行测试")
    parser.add_argument("-f", "--file", help="运行指定测试文件")
    parser.add_argument("--html", action="store_true", help="生成HTML测试报告")
    parser.add_argument("--reruns", type=int, default=0, help="失败重跑次数")
    parser.add_argument("-v", "--verbose", action="store_true", help="更详细的输出")
    parser.add_argument("--public-baseline", action="store_true", help="运行公开回归基线")
    sys.exit(run_pytest(parser.parse_args()))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest api_test/tests/test_run_test.py -v
```

Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add api_test/run_test.py api_test/tests/test_run_test.py
git commit -m "重构：修复 run_test.py 工作目录依赖并稳定公开基线入口"
```

---

### Task 5: Delete Legacy Private-Site Code And Normalize `api_test` Exports

**Files:**
- Delete: `api_test/config.py`
- Delete: `api_test/core/private_env.py`
- Delete: `api_test/core/public_api.py`
- Delete: `api_test/legacy_api_catalog.py`
- Delete: `api_test/core/legacy_assets.py`
- Delete: `api_test/tests/test_demo.py`
- Delete: `api_test/tests/test_public_api_governance.py`
- Delete: `api_test/test_data/account.txt`
- Modify: `api_test/core/__init__.py`

- [ ] **Step 1: Run the obsolete tests to confirm they no longer fit the generic framework**

Run:

```bash
python -m pytest api_test/tests/test_demo.py api_test/tests/test_public_api_governance.py -v
```

Expected: FAIL or import errors, proving these tests are invalid under the generic-framework target.

- [ ] **Step 2: Delete the private-site files and rewrite the exports**

```python
# api_test/core/__init__.py
"""Core exports for the generic api_test runtime."""

from core.base_api import BaseAPI
from core.jsonplaceholder_api import JsonPlaceholderAPI

__all__ = ["BaseAPI", "JsonPlaceholderAPI"]
```

Delete these files in the same change:

```text
api_test/config.py
api_test/core/private_env.py
api_test/core/public_api.py
api_test/legacy_api_catalog.py
api_test/core/legacy_assets.py
api_test/tests/test_demo.py
api_test/tests/test_public_api_governance.py
api_test/test_data/account.txt
```

- [ ] **Step 3: Run the full `api_test` suite after deletion**

Run:

```bash
python -m pytest api_test/tests -v
```

Expected: PASS with only config/base_api/jsonplaceholder/run_test related tests collected.

- [ ] **Step 4: Commit**

```bash
git add api_test/core/__init__.py
git rm api_test/config.py api_test/core/private_env.py api_test/core/public_api.py api_test/legacy_api_catalog.py api_test/core/legacy_assets.py api_test/tests/test_demo.py api_test/tests/test_public_api_governance.py api_test/test_data/account.txt
git commit -m "重构：删除旧私有站点链路与历史业务接口资产"
```

---

### Task 6: Remove The Hardcoded Legacy Bridge From `platform_core`

**Files:**
- Delete: `platform_core/legacy_assets.py`
- Modify: `platform_core/cli.py`
- Modify: `platform_core/services.py`
- Modify: `platform_core/rules.py`
- Test: `tests/platform_core/test_services_and_assets.py`
- Test: `tests/platform_core/test_templates_and_rules.py`

- [ ] **Step 1: Write the failing `platform_core` tests without legacy-bridge expectations**

```python
# tests/platform_core/test_templates_and_rules.py
import json
from datetime import datetime

from platform_core.models import ApiModule, ApiOperation, ApiParam, AssertionCandidate, GenerationRecord
from platform_core.renderers import TemplateRenderer
from platform_core.rules import RuleValidator


def build_module() -> ApiModule:
    return ApiModule(
        module_id="mod-user",
        module_name="user",
        module_code="user",
        module_path_hint="generated/apis/user_api.py",
        module_type="api",
        module_desc="用户模块",
        source_ids=["src-openapi-001"],
        tags=["user"],
    )


def build_operation() -> ApiOperation:
    return ApiOperation(
        operation_id="op-get-user",
        module_id="mod-user",
        operation_name="获取用户详情",
        operation_code="get_user_profile",
        http_method="GET",
        path="/api/users/{user_id}",
        summary="获取用户详情",
        description="根据用户 ID 查询用户资料",
        tags=["user"],
        auth_type=None,
        path_params=[
            ApiParam(
                param_id="param-path-user-id",
                operation_id="op-get-user",
                param_name="user_id",
                param_in="path",
                data_type="string",
                required=True,
                source="openapi",
            )
        ],
        query_params=[
            ApiParam(
                param_id="param-query-verbose",
                operation_id="op-get-user",
                param_name="verbose",
                param_in="query",
                data_type="boolean",
                required=False,
                default_value=False,
                source="openapi",
            )
        ],
        success_codes=[200],
        source_ids=["src-openapi-001"],
    )


def build_assertions() -> list[AssertionCandidate]:
    return [
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-get-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="openapi",
            confidence_score=1.0,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-json-001",
            operation_id="op-get-user",
            assertion_type="json_field_exists",
            target_path="data.id",
            expected_value=None,
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        ),
    ]


def test_api_template_renders_standard_api_module():
    renderer = TemplateRenderer()
    rendered = renderer.render_api_module(build_module(), [build_operation()])
    assert "class UserApi:" in rendered
    assert "def get_user_profile(self, user_id, verbose=False):" in rendered


def test_pytest_template_renders_basic_smoke_test():
    renderer = TemplateRenderer()
    rendered = renderer.render_test_module(build_module(), build_operation(), build_assertions())
    assert "def test_get_user_profile_smoke(api):" in rendered
    assert 'assert response["status_code"] == 200' in rendered


def test_generation_record_template_renders_traceable_json():
    renderer = TemplateRenderer()
    record = GenerationRecord(
        generation_id="gen-001",
        generation_type="api_method",
        source_ids=["src-openapi-001"],
        target_asset_type="api_module",
        target_asset_path="generated/apis/user_api.py",
        generator_type="hybrid",
        generated_at=datetime(2026, 3, 30, 10, 30, 0),
        generated_by="codex",
        generation_version="v1",
        template_reference="templates/api/api_module.py.j2",
        review_status="pending",
        execution_status="not_run",
    )
    payload = json.loads(renderer.render_generation_record(record))
    assert payload["source_ids"] == ["src-openapi-001"]


def test_rule_validator_rejects_invalid_operation_name():
    validator = RuleValidator()
    invalid_operation = build_operation().model_copy(update={"operation_code": "GetUserProfile"})
    violations = validator.validate_operation(invalid_operation)
    assert any("operation_code" in violation for violation in violations)


def test_rule_validator_rejects_missing_required_fields():
    validator = RuleValidator()
    invalid_operation = build_operation().model_copy(update={"http_method": "", "path": ""})
    violations = validator.validate_operation(invalid_operation)
    assert any("http_method" in violation for violation in violations)
    assert any("path" in violation for violation in violations)
```

```python
# tests/platform_core/test_services_and_assets.py
import json
import subprocess
import sys
from pathlib import Path

import pytest

from platform_core.pipeline import DocumentDrivenPipeline
from platform_core.services import PlatformApplicationService


def build_openapi_spec() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "paths": {
            "/api/users/{user_id}": {
                "get": {
                    "tags": ["user"],
                    "operationId": "getUserProfile",
                    "summary": "获取用户详情",
                    "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {
                            "description": "success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer", "example": 0},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string", "example": "u-100"},
                                                    "name": {"type": "string", "example": "Alice"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


def test_document_pipeline_persists_asset_manifest_with_hashes(tmp_path):
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"
    result = DocumentDrivenPipeline(project_root=Path.cwd()).run(source_path=source_path, output_root=output_root)
    manifest_path = output_root / "generated" / "records" / "asset_manifest.json"
    assert manifest_path.exists()
    assert result.asset_manifest_path == str(manifest_path)
    assert len(result.asset_manifest.assets) == 2


def test_platform_application_service_can_inspect_generated_workspace(tmp_path):
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"
    DocumentDrivenPipeline(project_root=Path.cwd()).run(source_path=source_path, output_root=output_root)
    inspection = PlatformApplicationService(project_root=Path.cwd()).inspect_workspace(output_root)
    assert inspection.validation_status == "valid"
    assert inspection.asset_count == 2
    assert inspection.generation_count == 2


def test_platform_core_cli_can_inspect_workspace_manifest(tmp_path):
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"
    DocumentDrivenPipeline(project_root=Path.cwd()).run(source_path=source_path, output_root=output_root)
    result = subprocess.run(
        [sys.executable, "-m", "platform_core.cli", "inspect", "--workspace", str(output_root)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_status"] == "valid"


def test_platform_application_service_blocks_future_routes_in_v1(tmp_path):
    service = PlatformApplicationService(project_root=Path.cwd())
    assert service.supported_routes()["document"] is True
    assert service.supported_routes()["functional_case"] is False
    assert service.supported_routes()["traffic_capture"] is False
    with pytest.raises(NotImplementedError):
        service.run_functional_case_pipeline(source_path=tmp_path / "cases.md", output_root=tmp_path / "out")
    with pytest.raises(NotImplementedError):
        service.run_traffic_capture_pipeline(source_path=tmp_path / "capture.har", output_root=tmp_path / "out")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py -v
```

Expected: FAIL because `cli.py`, `services.py`, and `rules.py` still expose legacy-public-api behavior.

- [ ] **Step 3: Write the minimal de-specialized `platform_core` runtime**

```python
# platform_core/services.py
from __future__ import annotations

from pathlib import Path

from platform_core.assets import AssetWorkspace
from platform_core.pipeline import DocumentDrivenPipeline
from platform_core.rules import RuleValidator


class PlatformApplicationService:
    """V1 应用服务层，当前仅开放文档驱动与工作区检查。"""

    def __init__(
        self,
        project_root: str | Path | None = None,
        document_pipeline: DocumentDrivenPipeline | None = None,
        validator: RuleValidator | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.document_pipeline = document_pipeline or DocumentDrivenPipeline(project_root=self.project_root)
        self.validator = validator or RuleValidator()

    @staticmethod
    def supported_routes() -> dict[str, bool]:
        return {"document": True, "functional_case": False, "traffic_capture": False}

    def run_document_pipeline(self, source_path: str | Path, output_root: str | Path):
        return self.document_pipeline.run(source_path=source_path, output_root=output_root)

    def inspect_workspace(self, output_root: str | Path):
        return AssetWorkspace(output_root).inspect_manifest(validator=self.validator)

    @staticmethod
    def run_functional_case_pipeline(source_path: str | Path, output_root: str | Path):
        raise NotImplementedError(f"V1 仅支持文档驱动最小闭环，暂不支持功能测试用例驱动: {source_path} -> {output_root}")

    @staticmethod
    def run_traffic_capture_pipeline(source_path: str | Path, output_root: str | Path):
        raise NotImplementedError(f"V1 仅支持文档驱动最小闭环，暂不支持抓包驱动: {source_path} -> {output_root}")
```

```python
# platform_core/cli.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

from platform_core.services import PlatformApplicationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="platform_core CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="执行文档驱动最小闭环")
    run_parser.add_argument("--source", required=True, help="OpenAPI/Swagger 文档路径")
    run_parser.add_argument("--output", required=True, help="输出工作目录")
    inspect_parser = subparsers.add_parser("inspect", help="检查已生成工作区的资产清单")
    inspect_parser.add_argument("--workspace", required=True, help="已生成工作区路径")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    service = PlatformApplicationService(project_root=Path.cwd())

    if args.command == "run":
        result = service.run_document_pipeline(source_path=args.source, output_root=args.output)
        print(json.dumps({
            "source": result.source_document.source_name,
            "modules": len(result.modules),
            "operations": len(result.operations),
            "execution_target": result.execution_record.target_id,
            "execution_status": result.execution_record.result_status,
            "report_path": result.execution_record.report_path,
            "asset_manifest_path": result.asset_manifest_path,
        }, ensure_ascii=False))
        return 0 if result.execution_record.result_status == "passed" else 1

    if args.command == "inspect":
        inspection = service.inspect_workspace(output_root=args.workspace)
        print(json.dumps(inspection.model_dump(mode="json"), ensure_ascii=False))
        return 0 if inspection.validation_status == "valid" else 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

```python
# platform_core/rules.py
from __future__ import annotations

import re
from pathlib import Path

from platform_core.models import ApiOperation, AssetManifest, AssertionCandidate, GenerationRecord


class RuleValidator:
    """V1 通用规则校验器。"""

    _SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

    def validate_operation(self, operation: ApiOperation) -> list[str]:
        violations: list[str] = []
        if not operation.operation_code or not self._SNAKE_CASE_PATTERN.match(operation.operation_code):
            violations.append("operation_code 必须为 snake_case")
        if not operation.module_id:
            violations.append("module_id 不能为空")
        if not operation.http_method:
            violations.append("http_method 不能为空")
        if not operation.path:
            violations.append("path 不能为空")
        if not operation.source_ids:
            violations.append("source_ids 不能为空")
        return violations

    @staticmethod
    def validate_test_file_name(file_name: str) -> list[str]:
        normalized = Path(file_name).name
        if not normalized.startswith("test_") or not normalized.endswith(".py"):
            return ["测试文件名必须符合 test_*.py 规范"]
        return []

    @staticmethod
    def validate_generation_record(record: GenerationRecord) -> list[str]:
        violations: list[str] = []
        if not record.source_ids:
            violations.append("generation_record.source_ids 不能为空")
        if not record.target_asset_path:
            violations.append("generation_record.target_asset_path 不能为空")
        if not record.template_reference:
            violations.append("generation_record.template_reference 不能为空")
        if not record.generation_version:
            violations.append("generation_record.generation_version 不能为空")
        if record.generator_type == "ai_assisted" and not record.prompt_reference:
            violations.append("ai_assisted 生成记录必须提供 prompt_reference")
        return violations

    @staticmethod
    def validate_assertions(operation: ApiOperation, assertions: list[AssertionCandidate]) -> list[str]:
        if operation.success_codes and not any(assertion.assertion_type == "status_code" for assertion in assertions):
            return ["可执行接口至少需要一个 status_code 断言"]
        return []

    @staticmethod
    def validate_asset_manifest(manifest: AssetManifest) -> list[str]:
        violations: list[str] = []
        if not manifest.assets:
            violations.append("asset_manifest.assets 不能为空")
        if not manifest.generation_ids:
            violations.append("asset_manifest.generation_ids 不能为空")
        if not manifest.execution_id:
            violations.append("asset_manifest.execution_id 不能为空")
        if not manifest.report_path:
            violations.append("asset_manifest.report_path 不能为空")
        for asset in manifest.assets:
            if not asset.source_ids:
                violations.append(f"asset_record.source_ids 不能为空: {asset.asset_id}")
            if not asset.content_digest:
                violations.append(f"asset_record.content_digest 不能为空: {asset.asset_id}")
        return violations


__all__ = ["RuleValidator"]
```

Delete in the same change:

```text
platform_core/legacy_assets.py
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py -v
```

Expected: PASS with no legacy-public-api-related collection or assertions.

- [ ] **Step 5: Commit**

```bash
git add platform_core/cli.py platform_core/services.py platform_core/rules.py tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py
git rm platform_core/legacy_assets.py
git commit -m "重构：移除 platform_core 对旧 PublicAPI 的硬编码桥接"
```

---

### Task 7: Update All Product, Architecture, And Usage Documents

**Files:**
- Modify: `README.md`
- Modify: `api_test/README.md`
- Modify: `api_test/QUICKSTART.md`
- Modify: `product_document/架构设计/总体架构设计说明书.md`
- Modify: `product_document/架构设计/现有接口自动化测试框架改造方案.md`
- Modify: `product_document/架构设计/中间模型设计说明书.md`
- Modify: `product_document/架构设计/模板体系与代码生成规范说明书.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [ ] **Step 1: Rewrite the root README around the generic framework**

```markdown
- 删除 README 中关于旧 `PublicAPI` 快照桥接、`inspect-legacy-public-api`、`snapshot-legacy-public-api`、`private_env` 与 RSA 的说明。
- 将 `api_test` 描述改成“通用 HTTP 测试底座 + JSON 配置驱动 + JSONPlaceholder 公开示例适配”。
- 将使用方式收敛为：
  - `python -m pytest tests/platform_core -v`
  - `python -m pytest api_test/tests -v`
  - `python api_test/run_test.py --public-baseline`
- 将最新基线改为本轮实际跑出的结果。
```

- [ ] **Step 2: Rewrite `api_test/README.md` and `api_test/QUICKSTART.md`**

```markdown
- 删除账号文件、管理员账号、私有环境登录、`ENABLE_PRIVATE_API_TESTS`、`API_TEST_RSA_PUBLIC_KEY` 相关段落。
- 新增 `api_config.json` 说明，列出 `runtime/session/execution/logging/site_profiles`。
- 快速入门示例统一改成 `JsonPlaceholderAPI` 用法。
- `run_test.py --public-baseline` 描述改成“执行带 `public_baseline` 标记的公开基线用例”。
```

- [ ] **Step 3: Rewrite product and V1 documents to remove private-site language**

```markdown
- 在《总体架构设计说明书》中，把 `api_test` 底座描述更新为“通用测试框架底座”，去掉旧 `PublicAPI` 桥接落地叙述。
- 在《现有接口自动化测试框架改造方案》中，把“拆分私有环境依赖”的阶段表述升级为“已删除私有站点链路，底座收口为通用配置驱动结构”。
- 在《中间模型设计说明书》中保留 `existing_api_asset` 概念，但去掉对旧 `PublicAPI` 目录的具体引用。
- 在《模板体系与代码生成规范说明书》中删除任何将旧私有接口目录视为当前实现成果的表述。
- 在《V1阶段工作计划文档》《V1实施计划与开发任务拆解说明书》《详细测试用例说明书(V1)》中：
  - 删除 `legacy_public_api` / `private_env` / RSA 风险项；
  - 删除 `inspect-legacy-public-api` / `snapshot-legacy-public-api` 任务与测试口径；
  - 新增“通用配置收口、公开基线正向标记、底座去特化”进度、测试结果与风险说明。
```

- [ ] **Step 4: Verify the docs no longer advertise removed private-site artifacts**

Run:

```bash
rg -n "PublicAPI|private_env|API_TEST_RSA_PUBLIC_KEY|inspect-legacy-public-api|snapshot-legacy-public-api|legacy_api_catalog" README.md api_test product_document
```

Expected: Only historical context intentionally retained in architecture docs; no active usage instructions or current-state claims.

- [ ] **Step 5: Commit**

```bash
git add README.md api_test/README.md api_test/QUICKSTART.md product_document/架构设计/总体架构设计说明书.md product_document/架构设计/现有接口自动化测试框架改造方案.md product_document/架构设计/中间模型设计说明书.md product_document/架构设计/模板体系与代码生成规范说明书.md product_document/阶段文档/V1阶段工作计划文档.md product_document/阶段文档/V1实施计划与开发任务拆解说明书.md product_document/测试文档/详细测试用例说明书(V1).md
git commit -m "文档：同步通用测试框架重构后的架构、阶段与使用说明"
```

---

### Task 8: Run Full Validation And Produce The Final Backup-Safe State

**Files:**
- Modify: whichever files remain staged from Tasks 1-7
- Test: full repo validation commands

- [ ] **Step 1: Run the `platform_core` full suite**

Run:

```bash
python -m pytest tests/platform_core -v
```

Expected: All `tests/platform_core` tests pass.

- [ ] **Step 2: Run the `api_test` full suite from the repository root**

Run:

```bash
python -m pytest api_test/tests -v
```

Expected: All `api_test/tests` tests pass.

- [ ] **Step 3: Run the public baseline entry from the repository root**

Run:

```bash
python api_test/run_test.py --public-baseline
```

Expected: The command completes successfully and only runs `public_baseline` tests under `api_test/tests`.

- [ ] **Step 4: Run the public baseline entry from inside `api_test/`**

Run:

```bash
cd api_test
python run_test.py --public-baseline
```

Expected: The command completes successfully with the same selected tests and the same pass result.

- [ ] **Step 5: Commit the final refactor state**

```bash
git add -A
git commit -m "重构：完成通用测试框架大改造并收口平台去特化逻辑"
```

- [ ] **Step 6: Push the completed refactor**

```bash
git push origin main
```
