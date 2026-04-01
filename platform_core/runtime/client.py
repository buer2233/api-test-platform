"""生成代码复用的最小请求客户端。"""

from __future__ import annotations

from typing import Any

import requests


class ApiClient:
    """生成代码使用的最小请求客户端。"""

    def __init__(self, base_url: str, timeout: int = 30):
        """初始化运行时客户端。"""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """发起请求，并统一返回状态码、JSON 和文本响应。"""
        url = f"{self.base_url}{path}"
        response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        try:
            payload: Any = response.json()
        except ValueError:
            payload = response.text
        return {
            "status_code": response.status_code,
            "json": payload,
            "text": response.text,
        }
