"""JSONPlaceholder 接口测试示例。"""

import pytest

from core.jsonplaceholder_api import JsonPlaceholderAPI


class TestJsonPlaceholderAPI:
    """JSONPlaceholder 公开站点基础测试。"""

    @pytest.fixture(scope="class")
    def api(self):
        api = JsonPlaceholderAPI()
        yield api
        api.session.close()

    @pytest.mark.basic
    @pytest.mark.smoke
    @pytest.mark.jsonplaceholder
    def test_get_single_post(self, api):
        """读取单条文章应返回稳定的基础字段。"""
        post = api.get_post(1)

        assert post["id"] == 1
        assert post["userId"] == 1
        assert isinstance(post["title"], str)
        assert isinstance(post["body"], str)

    @pytest.mark.basic
    @pytest.mark.jsonplaceholder
    def test_filter_posts_by_user_id(self, api):
        """过滤查询应只返回指定 userId 的文章。"""
        posts = api.list_user_posts(user_id=1)

        assert len(posts) > 0
        assert all(post["userId"] == 1 for post in posts)

    @pytest.mark.basic
    @pytest.mark.jsonplaceholder
    def test_nested_comments_route(self, api):
        """嵌套路由应返回指定文章的评论列表。"""
        comments = api.list_post_comments(post_id=1)

        assert len(comments) > 0
        assert all(comment["postId"] == 1 for comment in comments)
        assert all("email" in comment for comment in comments)

    @pytest.mark.P0
    @pytest.mark.regression
    @pytest.mark.jsonplaceholder
    def test_create_post_uses_fake_write_contract(self, api):
        """POST 应返回 201 和伪造资源标识。"""
        created = api.create_post(
            title="platform-core title",
            body="platform-core body",
            user_id=9,
        )

        assert created["title"] == "platform-core title"
        assert created["body"] == "platform-core body"
        assert created["userId"] == 9
        assert created["id"] == 101

    @pytest.mark.P0
    @pytest.mark.regression
    @pytest.mark.jsonplaceholder
    def test_put_replaces_post_payload(self, api):
        """PUT 应返回完整替换后的资源内容。"""
        updated = api.replace_post(
            post_id=1,
            title="replaced title",
            body="replaced body",
            user_id=3,
        )

        assert updated == {
            "id": 1,
            "title": "replaced title",
            "body": "replaced body",
            "userId": 3,
        }

    @pytest.mark.P0
    @pytest.mark.jsonplaceholder
    def test_patch_updates_partial_fields(self, api):
        """PATCH 应支持局部字段更新。"""
        updated = api.patch_post(1, title="patched title")

        assert updated["id"] == 1
        assert updated["title"] == "patched title"
        assert updated["userId"] == 1
        assert "body" in updated

    @pytest.mark.P0
    @pytest.mark.jsonplaceholder
    def test_delete_returns_empty_object(self, api):
        """DELETE 应返回成功状态和空对象。"""
        deleted = api.delete_post(1)

        assert deleted == {}
