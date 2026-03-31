"""JSONPlaceholder 公共测试站点 API 封装。"""

from __future__ import annotations

from typing import Any

from core.base_api import BaseAPI


class JsonPlaceholderAPI(BaseAPI):
    """面向 JSONPlaceholder 的公开测试 API 封装。"""

    def list_posts(self, **params) -> list[dict[str, Any]]:
        return self.get("/posts", params=params)

    def get_post(self, post_id: int) -> dict[str, Any]:
        return self.get(f"/posts/{post_id}")

    def list_post_comments(self, post_id: int) -> list[dict[str, Any]]:
        return self.get(f"/posts/{post_id}/comments")

    def list_user_posts(self, user_id: int) -> list[dict[str, Any]]:
        return self.get("/posts", params={"userId": user_id})

    def create_post(self, title: str, body: str, user_id: int) -> dict[str, Any]:
        return self.post(
            "/posts",
            json={"title": title, "body": body, "userId": user_id},
            expected_status=201,
        )

    def replace_post(self, post_id: int, title: str, body: str, user_id: int) -> dict[str, Any]:
        return self.request(
            "PUT",
            f"/posts/{post_id}",
            json={"id": post_id, "title": title, "body": body, "userId": user_id},
        )

    def patch_post(self, post_id: int, **fields: Any) -> dict[str, Any]:
        return self.request("PATCH", f"/posts/{post_id}", json=fields)

    def delete_post(self, post_id: int) -> dict[str, Any]:
        return self.delete(f"/posts/{post_id}")
