"""Generic HTTP API base client for public and internal site adapters."""

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
    """Generic HTTP API client with shared utility helpers."""

    def __init__(self) -> None:
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
        if isinstance(expected_status, int):
            return (expected_status,)
        normalized = tuple(expected_status)
        assert normalized, "expected_status 不能为空"
        return normalized

    def get(self, url: str, **kwargs: Any) -> Any:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> Any:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Any:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Any:
        return self.request("DELETE", url, **kwargs)

    @staticmethod
    def get_value(data: Any, keys: list[str] | str, msg: str = "") -> Any:
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
        fmt = "%Y-%m-%d" if is_all_day else "%Y-%m-%d %H:%M:%S"
        return str(int(time.mktime(time.strptime(date_str, fmt)) * 1000))

    @staticmethod
    def stamp_to_time(timestamp: int) -> str:
        normalized = int(timestamp / 1000) if len(str(timestamp)) == 13 else timestamp
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(normalized))

    @staticmethod
    def get_week_info(day: date | str | None = None) -> tuple[str, str]:
        if day is None:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, "%Y-%m-%d").date()
        monday = day - timedelta(days=day.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    @staticmethod
    def get_month_info(day: date | str | None = None) -> tuple[str, str, int]:
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
        digest = hashlib.md5()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest().lower()

    @staticmethod
    def sha1_encrypt(text: str) -> str:
        digest = hashlib.sha1()
        digest.update(text.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def aes_ecb_encrypt(plain_text: str, key: str) -> str:
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def aes_ecb_decrypt(cipher_text: str, key: str) -> str:
        cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
        encrypted = base64.b64decode(cipher_text)
        return unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8")

    @staticmethod
    def aes_cbc_encrypt(plain_text: str, key: str, iv: str) -> str:
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def aes_cbc_decrypt(cipher_text: str, key: str, iv: str) -> str:
        cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
        encrypted = base64.b64decode(cipher_text)
        return unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8")

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        population = string.ascii_lowercase + string.digits
        return "".join(random.sample(population, length))

    @staticmethod
    def generate_phone_number() -> str:
        second = random.choice([3, 4, 5, 7, 8])
        third = random.choice(list(range(10)))
        suffix = random.randint(10000000, 99999999)
        return f"1{second}{third}{suffix}"

    @staticmethod
    def generate_email(prefix: str | None = None) -> str:
        prefix = prefix or BaseAPI.generate_random_string(8)
        return f"{prefix}{int(time.time() * 1000)}@etest.com"
