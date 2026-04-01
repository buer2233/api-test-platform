"""JSONPlaceholder 公共测试站点 API 封装。"""

from __future__ import annotations

from typing import Any

from core.base_api import BaseAPI


class JsonPlaceholderAPI(BaseAPI):
    """面向 JSONPlaceholder 的公开测试 API 封装。"""

    def list_posts(self, **params) -> list[dict[str, Any]]:
        """查询文章列表，并支持透传过滤参数。"""
        return self.get("/posts", params=params)

    def get_post(self, post_id: int) -> dict[str, Any]:
        """查询单篇文章详情。"""
        return self.get(f"/posts/{post_id}")

    def list_post_comments(self, post_id: int) -> list[dict[str, Any]]:
        """查询某篇文章下的评论列表。"""
        return self.get(f"/posts/{post_id}/comments")

    def list_user_posts(self, user_id: int) -> list[dict[str, Any]]:
        """查询指定用户发布的文章列表。"""
        return self.get("/posts", params={"userId": user_id})

    def list_users(self) -> list[dict[str, Any]]:
        """查询用户列表。"""
        return self.get("/users")

    def get_user(self, user_id: int) -> dict[str, Any]:
        """查询单个用户详情。"""
        return self.get(f"/users/{user_id}")

    def list_todos(self, **params) -> list[dict[str, Any]]:
        """查询待办列表，并支持透传过滤参数。"""
        return self.get("/todos", params=params)

    def list_user_todos(self, user_id: int) -> list[dict[str, Any]]:
        """查询指定用户的待办列表。"""
        return self.get(f"/users/{user_id}/todos")

    def create_post(self, title: str, body: str, user_id: int) -> dict[str, Any]:
        """创建文章，并按 JSONPlaceholder 的伪写入契约断言 201。"""
        return self.post(
            "/posts",
            json={"title": title, "body": body, "userId": user_id},
            expected_status=201,
        )

    def replace_post(self, post_id: int, title: str, body: str, user_id: int) -> dict[str, Any]:
        """整体替换文章内容。"""
        return self.put(
            f"/posts/{post_id}",
            json={"id": post_id, "title": title, "body": body, "userId": user_id},
        )

    def patch_post(self, post_id: int, **fields: Any) -> dict[str, Any]:
        """局部更新文章字段。"""
        return self.patch(f"/posts/{post_id}", json=fields)

    def delete_post(self, post_id: int) -> dict[str, Any]:
        """删除文章，并返回 JSONPlaceholder 的空对象响应。"""
        return self.delete(f"/posts/{post_id}")
