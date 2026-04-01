import json
from pathlib import Path

import pytest
import requests

import core.config_loader as config_loader
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


def test_build_retry_session_retries_transport_failures_for_all_methods():
    config = get_api_config()

    session = build_retry_session()
    retry_policy = session.adapters["https://"].max_retries

    assert retry_policy.total == config.session.max_retries
    assert retry_policy.connect == config.session.max_retries
    assert retry_policy.read == config.session.max_retries
    assert retry_policy.allowed_methods is None
    session.close()


def test_build_retry_session_applies_proxy_when_enabled(tmp_path, monkeypatch):
    payload = json.loads((Path(__file__).resolve().parents[1] / "api_config.json").read_text(encoding="utf-8"))
    payload["proxy"] = {"enabled": True, "url": "http://127.0.0.1:7890"}
    config_path = tmp_path / "api_config.json"
    config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setattr(config_loader, "_CONFIG_CACHE", config_loader.load_api_config(config_path))

    session = build_retry_session()

    assert session.proxies["http"] == "http://127.0.0.1:7890"
    assert session.proxies["https"] == "http://127.0.0.1:7890"
    session.close()
    clear_api_config_cache()


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
