"""JSONPlaceholder 公开基线接口测试。"""

import pytest


pytestmark = [pytest.mark.jsonplaceholder, pytest.mark.public_baseline]


class TestJsonPlaceholderAPI:
    """公开文章资源与写操作契约测试集合。"""

    def test_get_single_post(self, jsonplaceholder_api):
        """校验可获取单篇文章详情。"""
        payload = jsonplaceholder_api.get_post(1)

        assert payload["id"] == 1

    def test_filter_posts_by_user_id(self, jsonplaceholder_api):
        """校验文章列表支持按用户过滤。"""
        payload = jsonplaceholder_api.list_posts(userId=1)

        assert payload
        assert all(item["userId"] == 1 for item in payload)

    def test_nested_comments_route(self, jsonplaceholder_api):
        """校验文章评论支持嵌套路由访问。"""
        payload = jsonplaceholder_api.list_post_comments(1)

        assert payload
        assert all(item["postId"] == 1 for item in payload)

    def test_create_post_uses_fake_write_contract(self, jsonplaceholder_api):
        """校验创建文章遵循 JSONPlaceholder 的伪写入契约。"""
        payload = jsonplaceholder_api.create_post(title="demo", body="payload", user_id=1)

        assert payload["title"] == "demo"
        assert payload["id"] == 101

    def test_put_replaces_post_payload(self, jsonplaceholder_api):
        """校验 PUT 会返回替换后的文章内容。"""
        payload = jsonplaceholder_api.replace_post(1, title="new", body="body", user_id=1)

        assert payload["id"] == 1
        assert payload["title"] == "new"

    def test_patch_updates_partial_fields(self, jsonplaceholder_api):
        """校验 PATCH 支持局部更新文章字段。"""
        payload = jsonplaceholder_api.patch_post(1, title="patched")

        assert payload["title"] == "patched"

    def test_delete_returns_empty_object(self, jsonplaceholder_api):
        """校验删除文章时返回空对象响应。"""
        payload = jsonplaceholder_api.delete_post(1)

        assert payload == {}
