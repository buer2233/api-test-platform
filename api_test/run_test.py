"""Stable pytest launcher for the generic api_test suite."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from core.config_loader import get_api_config


def get_api_test_root() -> Path:
    return Path(__file__).resolve().parent


def get_tests_root() -> Path:
    return get_api_test_root() / get_api_config().execution.tests_root


def get_pytest_config_path() -> Path:
    return get_api_test_root() / "pytest.ini"


def build_pytest_command(args) -> list[str]:
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
    command = build_pytest_command(args)
    print(f"执行命令: {' '.join(command)}")
    return subprocess.run(command, cwd=get_api_test_root()).returncode


def main() -> None:
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
