"""通用工具模块回归测试。"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


def load_common_tools_module():
    """按文件路径加载 `common_tools` 模块，避免在红灯阶段发生导入级报错。"""
    module_path = Path(__file__).resolve().parents[1] / "core" / "common_tools.py"
    assert module_path.exists(), "common_tools.py 应作为 BaseAPI 工具拆分承接模块存在"
    spec = importlib.util.spec_from_file_location("core.common_tools", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_common_tools_module_exposes_expected_functions():
    """校验工具模块暴露了本轮迁移要求的通用函数。"""
    common_tools = load_common_tools_module()
    expected_functions = [
        "get_value",
        "time_to_stamp",
        "stamp_to_time",
        "get_week_info",
        "get_month_info",
        "md5_encrypt",
        "sha1_encrypt",
        "aes_ecb_encrypt",
        "aes_ecb_decrypt",
        "aes_cbc_encrypt",
        "aes_cbc_decrypt",
        "generate_random_string",
        "generate_phone_number",
        "generate_email",
    ]

    for function_name in expected_functions:
        assert hasattr(common_tools, function_name), f"缺少通用工具函数：{function_name}"


def test_get_value_supports_nested_dict_and_list_paths():
    """校验嵌套字典与列表路径提取逻辑保持可用。"""
    common_tools = load_common_tools_module()
    payload = {"users": [{"profile": {"name": "alice"}}]}

    result = common_tools.get_value(payload, ["users", 0, "profile", "name"])

    assert result == "alice"


def test_get_value_raises_assertion_for_missing_path():
    """校验缺失路径会抛出可读的断言错误。"""
    common_tools = load_common_tools_module()

    with pytest.raises(AssertionError, match="数据中不存在路径"):
        common_tools.get_value({"users": []}, ["users", 1, "name"])


def test_time_helpers_convert_between_text_and_timestamp():
    """校验时间文本与时间戳之间可以往返转换。"""
    common_tools = load_common_tools_module()

    timestamp = common_tools.time_to_stamp("2024-03-01 12:30:45")

    assert timestamp.isdigit()
    assert common_tools.stamp_to_time(int(timestamp)) == "2024-03-01 12:30:45"


def test_calendar_helpers_return_expected_ranges():
    """校验周范围和月范围计算结果正确。"""
    common_tools = load_common_tools_module()

    week_start, week_end = common_tools.get_week_info("2024-03-06")
    month_start, month_end, total_days = common_tools.get_month_info("2024-02-06")

    assert (week_start, week_end) == ("2024-03-04", "2024-03-10")
    assert (month_start, month_end, total_days) == ("2024-02-01", "2024-02-29", 29)


def test_hash_helpers_return_expected_digest_values():
    """校验哈希工具迁移后仍保持原有输出。"""
    common_tools = load_common_tools_module()

    assert common_tools.md5_encrypt("abc") == "900150983cd24fb0d6963f7d28e17f72"
    assert common_tools.sha1_encrypt("abc") == "a9993e364706816aba3e25717850c26c9cd0d89d"


def test_aes_helpers_support_round_trip_for_ecb_and_cbc():
    """校验 AES ECB 和 CBC 工具都能正确往返。"""
    common_tools = load_common_tools_module()
    plain_text = "hello-platform"
    key = "1234567890abcdef"
    iv = "fedcba0987654321"

    ecb_cipher = common_tools.aes_ecb_encrypt(plain_text, key)
    cbc_cipher = common_tools.aes_cbc_encrypt(plain_text, key, iv)

    assert common_tools.aes_ecb_decrypt(ecb_cipher, key) == plain_text
    assert common_tools.aes_cbc_decrypt(cbc_cipher, key, iv) == plain_text


def test_random_data_helpers_generate_expected_format():
    """校验随机数据工具生成值的格式符合预期。"""
    common_tools = load_common_tools_module()

    random_text = common_tools.generate_random_string(12)
    phone_number = common_tools.generate_phone_number()
    email = common_tools.generate_email("tester")

    assert len(random_text) == 12
    assert re.fullmatch(r"[a-z0-9]{12}", random_text)
    assert re.fullmatch(r"1[34578]\d\d{8}", phone_number)
    assert email.startswith("tester")
    assert email.endswith("@etest.com")
