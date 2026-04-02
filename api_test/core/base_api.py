"""通用 HTTP API 基类。"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from core.config_loader import get_api_config
from core.session import build_retry_session


class BaseAPI:
    """通用 HTTP API 客户端，仅保留请求相关能力。"""

    def __init__(self) -> None:
        """根据唯一配置源初始化请求会话、基础地址和默认请求头。"""
        config = get_api_config()
        self.base_url = config.runtime.base_url.rstrip("/")
        self.timeout = config.runtime.timeout
        self.verify_ssl = config.runtime.verify_ssl
        self.default_headers = dict(config.runtime.default_headers)
        self.session = build_retry_session()

    def request(
        self,
        method: str,
        url: str,
        expected_status: int | Iterable[int] = 200,
        **kwargs: Any,
    ) -> Any:
        """发起一次 HTTP 请求并校验响应状态码。

        参数说明：
        - `method`：HTTP 方法，例如 `GET`、`POST`。
        - `url`：相对路径或完整 URL；相对路径会自动拼接 `base_url`。
        - `expected_status`：允许的状态码，可以是单个整数或状态码集合。
        - `kwargs`：透传给 `requests.Session.request` 的参数；其中 `NOTJSON`
          为框架兼容参数，表示直接返回原始 `Response` 对象。
        """
        not_json = bool(kwargs.pop("NOTJSON", False))
        allowed_statuses = self._normalize_expected_status(expected_status)
        headers = dict(self.default_headers)
        headers.update(kwargs.pop("headers", {}))
        final_url = url if url.startswith(("http://", "https://")) else f"{self.base_url}/{url.lstrip('/')}"
        response = self.session.request(
            method=method.upper(),
            url=final_url,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify_ssl,
            **kwargs,
        )
        assert response.status_code in allowed_statuses, (
            f"请求失败: {method} {final_url}\n"
            f"状态码: {response.status_code}, 期望: {allowed_statuses}\n"
            f"响应: {response.text}"
        )
        return response if not_json else response.json()

    @staticmethod
    def _normalize_expected_status(expected_status: int | Iterable[int]) -> tuple[int, ...]:
        """把期望状态码统一转换为元组，便于后续断言。"""
        if isinstance(expected_status, int):
            return (expected_status,)
        normalized = tuple(expected_status)
        assert normalized, "expected_status 不能为空"
        return normalized

    def get(self, url: str, **kwargs: Any) -> Any:
        """发送 GET 请求。"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        """发送 POST 请求。"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Any:
        """发送 PUT 请求。"""
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Any:
        """发送 PATCH 请求。"""
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Any:
        """发送 DELETE 请求。"""
        return self.request("DELETE", url, **kwargs)
