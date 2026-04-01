"""`run_test.py` 执行命令构建测试。"""

from argparse import Namespace
from pathlib import Path

import run_test


def test_build_pytest_command_supports_public_baseline_filter():
    """校验公开基线开关会生成对应 marker 过滤条件。"""
    args = Namespace(mark=None, file=None, html=False, reruns=0, verbose=False, public_baseline=True)

    command = run_test.build_pytest_command(args)

    assert command[:5] == [
        "pytest",
        "-v",
        "-c",
        str(run_test.get_pytest_config_path()),
        str(run_test.get_tests_root()),
    ]
    assert command[5:7] == ["-m", "public_baseline"]


def test_build_pytest_command_combines_marker_with_public_baseline():
    """校验自定义 marker 与公开基线 marker 会被正确组合。"""
    args = Namespace(
        mark="jsonplaceholder",
        file="tests/test_jsonplaceholder_api.py",
        html=True,
        reruns=2,
        verbose=True,
        public_baseline=True,
    )

    command = run_test.build_pytest_command(args)

    assert command[:2] == ["pytest", "-vv"]
    assert command[2:6] == ["-c", str(run_test.get_pytest_config_path()), str(run_test.get_tests_root()), "-m"]
    assert command[6] == "(jsonplaceholder) and public_baseline"
    assert str(Path("tests/test_jsonplaceholder_api.py")) in command
    assert "--html" in command
    assert "--reruns" in command
