"""通用 HTTP API 基类。"""

from __future__ import annotations

import base64
import hashlib
import random
import string
import time
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from core.config_loader import get_api_config
from core.session import build_retry_session


class BaseAPI:
    """通用 HTTP API 客户端，并保留少量通用工具方法。"""

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

    @staticmethod
    def get_value(data: Any, keys: list[str] | str, msg: str = "") -> Any:
        """按路径提取嵌套字典或列表中的值。"""
        path = keys if isinstance(keys, list) else [keys]
        try:
            for key in path:
                data = data[key]
            return data
        except (KeyError, IndexError, TypeError) as exc:
            error_msg = f"数据中不存在路径 '{path}'"
            if msg:
                error_msg = f"{msg}: {error_msg}"
            raise AssertionError(error_msg) from exc

    @staticmethod
    def time_to_stamp(date_str: str, is_all_day: bool = False) -> str:
        """把日期字符串转换为毫秒级时间戳字符串。"""
        fmt = "%Y-%m-%d" if is_all_day else "%Y-%m-%d %H:%M:%S"
        return str(int(time.mktime(time.strptime(date_str, fmt)) * 1000))

    @staticmethod
    def stamp_to_time(timestamp: int) -> str:
        """把秒或毫秒级时间戳转换为标准时间字符串。"""
        normalized = int(timestamp / 1000) if len(str(timestamp)) == 13 else timestamp
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(normalized))

    @staticmethod
    def get_week_info(day: date | str | None = None) -> tuple[str, str]:
        """获取指定日期所在周的周一和周日。"""
        if day is None:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, "%Y-%m-%d").date()
        monday = day - timedelta(days=day.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    @staticmethod
    def get_month_info(day: date | str | None = None) -> tuple[str, str, int]:
        """获取指定日期所在月份的起止日期和总天数。"""
        if day is None:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, "%Y-%m-%d").date()
        first_day = date(day.year, day.month, 1)
        next_month = date(day.year + 1, 1, 1) if day.month == 12 else date(day.year, day.month + 1, 1)
        last_day = next_month - timedelta(days=1)
        total_days = (last_day - first_day).days + 1
        return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"), total_days

    @staticmethod
    def md5_encrypt(text: str) -> str:
        """计算字符串的 MD5 摘要。"""
        digest = hashlib.md5()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest().lower()

    @staticmethod
    def sha1_encrypt(text: str) -> str:
        """计算字符串的 SHA1 摘要。"""
        digest = hashlib.sha1()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def aes_ecb_encrypt(plain_text: str, key: str) -> str:
        """使用 AES-ECB 模式加密字符串。"""
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def aes_ecb_decrypt(cipher_text: str, key: str) -> str:
        """使用 AES-ECB 模式解密字符串。"""
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        encrypted = base64.b64decode(cipher_text)
        return unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8")

    @staticmethod
    def aes_cbc_encrypt(plain_text: str, key: str, iv: str) -> str:
        """使用 AES-CBC 模式加密字符串。"""
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def aes_cbc_decrypt(cipher_text: str, key: str, iv: str) -> str:
        """使用 AES-CBC 模式解密字符串。"""
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        encrypted = base64.b64decode(cipher_text)
        return unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8")

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """生成指定长度的随机字符串。"""
        population = string.ascii_lowercase + string.digits
        return "".join(random.sample(population, length))

    @staticmethod
    def generate_phone_number() -> str:
        """生成一个模拟手机号。"""
        second = random.choice([3, 4, 5, 7, 8])
        third = random.choice(list(range(10)))
        suffix = random.randint(10000000, 99999999)
        return f"1{second}{third}{suffix}"

    @staticmethod
    def generate_email(prefix: str | None = None) -> str:
        """生成一个唯一邮箱地址，常用于测试数据。"""
        prefix = prefix or BaseAPI.generate_random_string(8)
        return f"{prefix}{int(time.time() * 1000)}@etest.com"
