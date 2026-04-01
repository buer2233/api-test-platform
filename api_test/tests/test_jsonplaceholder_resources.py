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
