"""`api_test` 测试执行入口。

本文件负责把命令行参数转换为稳定的 pytest 调用命令，并统一读取
`api_config.json` 中的执行配置。后续客户端接入时，也应复用这里的
参数含义和执行约束，而不是另起一套平行配置。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from core.config_loader import get_api_config


def get_api_test_root() -> Path:
    """返回 `api_test` 目录根路径，供执行入口统一定位配置和测试目录。"""
    return Path(__file__).resolve().parent


def get_tests_root() -> Path:
    """根据唯一配置源计算测试目录路径。"""
    return get_api_test_root() / get_api_config().execution.tests_root


def get_pytest_config_path() -> Path:
    """返回当前执行入口使用的 pytest 配置文件路径。"""
    return get_api_test_root() / "pytest.ini"


def build_pytest_command(args) -> list[str]:
    """构建 pytest 命令。

    参数说明：
    - `args.mark`：用户显式传入的 pytest marker 表达式。
    - `args.public_baseline`：是否强制收口到公开基线 marker。
    - `args.file`：定向执行的单个测试文件。
    - `args.html`：是否生成 HTML 报告。
    - `args.reruns`：失败重跑次数。
    - `args.verbose`：是否使用更详细的输出级别。
    """
    config = get_api_config()
    command = [
        "pytest",
        "-vv" if args.verbose else "-v",
        "-c",
        str(get_pytest_config_path()),
        str(get_tests_root()),
    ]
    marker_expression = args.mark
    if args.public_baseline:
        public_expression = config.execution.public_baseline_marker
        marker_expression = f"({marker_expression}) and {public_expression}" if marker_expression else public_expression
    if marker_expression:
        command.extend(["-m", marker_expression])
    if args.file:
        command.append(str(Path(args.file)))
    if args.html:
        report_dir = get_api_test_root() / config.execution.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        command.extend(["--html", str(report_dir / "report.html"), "--self-contained-html"])
    if args.reruns:
        command.extend(["--reruns", str(args.reruns)])
    return command


def run_pytest(args) -> int:
    """执行构建好的 pytest 命令，并把命令内容打印给调用方。"""
    command = build_pytest_command(args)
    print(f"执行命令: {' '.join(command)}")
    return subprocess.run(command, cwd=get_api_test_root()).returncode


def main() -> None:
    """解析命令行参数并退出到对应 pytest 返回码。"""
    parser = argparse.ArgumentParser(description="接口自动化测试运行器")
    parser.add_argument("-m", "--mark", help="按标记运行测试")
    parser.add_argument("-f", "--file", help="运行指定测试文件")
    parser.add_argument("--html", action="store_true", help="生成HTML测试报告")
    parser.add_argument("--reruns", type=int, default=0, help="失败重跑次数")
    parser.add_argument("-v", "--verbose", action="store_true", help="更详细的输出")
    parser.add_argument("--public-baseline", action="store_true", help="运行公开回归基线")
    sys.exit(run_pytest(parser.parse_args()))


if __name__ == "__main__":
    main()
