"""通用工具函数模块。"""

from __future__ import annotations

import base64
import hashlib
import random
import string
import time
from datetime import date, datetime, timedelta
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

__all__ = [
    "aes_cbc_decrypt",
    "aes_cbc_encrypt",
    "aes_ecb_decrypt",
    "aes_ecb_encrypt",
    "generate_email",
    "generate_phone_number",
    "generate_random_string",
    "get_month_info",
    "get_value",
    "get_week_info",
    "md5_encrypt",
    "sha1_encrypt",
    "stamp_to_time",
    "time_to_stamp",
]


def get_value(data: Any, keys: list[Any] | tuple[Any, ...] | Any, msg: str = "") -> Any:
    """按路径提取嵌套字典或列表中的值。

    参数说明：
    - `data`：待提取的原始数据对象。
    - `keys`：路径列表、路径元组或单个键值。
    - `msg`：断言失败时追加的中文提示。
    """
    path = list(keys) if isinstance(keys, (list, tuple)) else [keys]
    try:
        for key in path:
            data = data[key]
        return data
    except (KeyError, IndexError, TypeError) as exc:
        error_msg = f"数据中不存在路径 '{path}'"
        if msg:
            error_msg = f"{msg}: {error_msg}"
        raise AssertionError(error_msg) from exc


def time_to_stamp(date_str: str, is_all_day: bool = False) -> str:
    """把日期字符串转换为毫秒级时间戳字符串。"""
    fmt = "%Y-%m-%d" if is_all_day else "%Y-%m-%d %H:%M:%S"
    return str(int(time.mktime(time.strptime(date_str, fmt)) * 1000))


def stamp_to_time(timestamp: int) -> str:
    """把秒或毫秒级时间戳转换为标准时间字符串。"""
    normalized = int(timestamp / 1000) if len(str(timestamp)) == 13 else timestamp
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(normalized))


def get_week_info(day: date | str | None = None) -> tuple[str, str]:
    """获取指定日期所在周的周一和周日。"""
    if day is None:
        day = date.today()
    elif isinstance(day, str):
        day = datetime.strptime(day, "%Y-%m-%d").date()
    monday = day - timedelta(days=day.weekday())
    sunday = monday + timedelta(days=6)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


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


def md5_encrypt(text: str) -> str:
    """计算字符串的 MD5 摘要。"""
    digest = hashlib.md5()
    digest.update(text.encode("utf-8"))
    return digest.hexdigest().lower()


def sha1_encrypt(text: str) -> str:
    """计算字符串的 SHA1 摘要。"""
    digest = hashlib.sha1()
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def aes_ecb_encrypt(plain_text: str, key: str) -> str:
    """使用 AES-ECB 模式加密字符串。"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def aes_ecb_decrypt(cipher_text: str, key: str) -> str:
    """使用 AES-ECB 模式解密字符串。"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    encrypted = base64.b64decode(cipher_text)
    return unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8")


def aes_cbc_encrypt(plain_text: str, key: str, iv: str) -> str:
    """使用 AES-CBC 模式加密字符串。"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    encrypted = cipher.encrypt(pad(plain_text.encode("utf-8"), AES.block_size))
    return base64.b64encode(encrypted).decode("utf-8")


def aes_cbc_decrypt(cipher_text: str, key: str, iv: str) -> str:
    """使用 AES-CBC 模式解密字符串。"""
    cipher = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    encrypted = base64.b64decode(cipher_text)
    return unpad(cipher.decrypt(encrypted), AES.block_size).decode("utf-8")


def generate_random_string(length: int = 10) -> str:
    """生成指定长度的随机字符串。"""
    population = string.ascii_lowercase + string.digits
    return "".join(random.sample(population, length))


def generate_phone_number() -> str:
    """生成一个模拟手机号。"""
    second = random.choice([3, 4, 5, 7, 8])
    third = random.choice(list(range(10)))
    suffix = random.randint(10000000, 99999999)
    return f"1{second}{third}{suffix}"


def generate_email(prefix: str | None = None) -> str:
    """生成一个唯一邮箱地址，常用于测试数据。"""
    actual_prefix = prefix or generate_random_string(8)
    return f"{actual_prefix}{int(time.time() * 1000)}@etest.com"
