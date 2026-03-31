import base64

import pytest
import requests
import rsa

from core.base_api import BaseAPI
from core.session import build_retry_session


def test_build_retry_session_mounts_http_and_https_adapters():
    session = build_retry_session(pool_connections=12, pool_maxsize=34, max_retries=5)

    assert isinstance(session.adapters["http://"], requests.adapters.HTTPAdapter)
    assert isinstance(session.adapters["https://"], requests.adapters.HTTPAdapter)
    assert session.adapters["http://"]._pool_connections == 12
    assert session.adapters["https://"]._pool_maxsize == 34
    session.close()


def test_password_rsa_requires_configured_public_key(monkeypatch):
    monkeypatch.delenv("API_TEST_RSA_PUBLIC_KEY", raising=False)

    with pytest.raises(RuntimeError, match="API_TEST_RSA_PUBLIC_KEY"):
        BaseAPI.password_rsa("Secret123")


def test_password_rsa_uses_configured_public_key(monkeypatch):
    public_key, private_key = rsa.newkeys(512)
    monkeypatch.setenv("API_TEST_RSA_PUBLIC_KEY", public_key.save_pkcs1(format="PEM").decode("utf-8"))

    encrypted = BaseAPI.password_rsa("Secret123")
    decrypted = rsa.decrypt(base64.b64decode(encrypted), private_key).decode("utf-8")

    assert decrypted == "Secret123"


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


def test_request_accepts_non_200_expected_status(monkeypatch):
    class DummyResponse:
        status_code = 201

        @staticmethod
        def json():
            return {"id": 101}

        text = '{"id": 101}'

    api = BaseAPI()
    monkeypatch.setattr(api.session, "request", lambda **kwargs: DummyResponse())

    response = api.post("/posts", expected_status=201)

    assert response["id"] == 101
    api.session.close()


def test_request_rejects_unexpected_status_from_allowed_set(monkeypatch):
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
