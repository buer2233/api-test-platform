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
