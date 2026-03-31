import pytest

from core.public_api import PublicAPI


def test_public_api_exposes_governed_operation_catalog():
    operations = PublicAPI.describe_operations()

    assert "invite_user" in operations
    assert "get_team_info" in operations
    invite_user = operations["invite_user"]

    assert invite_user.operation_code == "invite_user"
    assert invite_user.module_code == "user_management"
    assert invite_user.http_method == "POST"
    assert invite_user.path_template == "/api/basicserver/saves"
    assert invite_user.requires_private_env is True


def test_invite_user_routes_through_governed_operation(monkeypatch):
    api = PublicAPI()
    captured = {}

    def fake_request(method, url, eteamsid=None, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["eteamsid"] = eteamsid
        captured["kwargs"] = kwargs
        return {"inviteInfos": [{"initPassword": "Init123456"}]}

    monkeypatch.setattr(api, "request", fake_request)

    result = api.invite_user("sid-001", "Alice", "alice@example.com")

    assert captured["method"] == "POST"
    assert captured["url"] == "/api/basicserver/saves"
    assert captured["eteamsid"] == "sid-001"
    assert captured["kwargs"]["json"]["inviteInfos"][0]["invitee"] == "Alice"
    assert result["success"] is True
    assert result["password"] == "Init123456"
    api.session.close()


def test_send_remind_uses_raw_response_mode(monkeypatch):
    class DummyResponse:
        status_code = 204
        text = ""

    api = PublicAPI()
    captured = {}

    def fake_request(method, url, eteamsid=None, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["eteamsid"] = eteamsid
        captured["kwargs"] = kwargs
        return DummyResponse()

    monkeypatch.setattr(api, "request", fake_request)

    status_code = api.send_remind("sid-002", "target-001", content="follow up")

    assert status_code == 204
    assert captured["method"] == "POST"
    assert captured["url"] == "/api/bcw/remind/send"
    assert captured["kwargs"]["NOTJSON"] is True
    assert captured["kwargs"]["json"]["targetId"] == "target-001"
    api.session.close()
