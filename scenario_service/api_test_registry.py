"""`api_test` 接口方法注册扫描能力。"""

from __future__ import annotations


class ApiTestMethodRegistry:
    """按 HTTP 方法和完整 URL 路径管理已有接口方法。"""

    def __init__(self) -> None:
        """初始化空注册表。"""
        self._items: dict[tuple[str, str], dict] = {}

    def register(self, item: dict) -> None:
        """注册一个已有接口方法定义。"""
        key = (str(item["http_method"]).upper(), str(item["full_path"]))
        self._items[key] = item

    def match(self, http_method: str, full_path: str) -> dict | None:
        """按 HTTP 方法和完整路径返回命中的接口方法。"""
        return self._items.get((http_method.upper(), full_path))
