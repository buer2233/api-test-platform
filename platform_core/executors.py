"""pytest 执行器实现。"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from platform_core.models import ExecutionRecord


class PytestExecutor:
    """最小 pytest 执行器。"""

    def __init__(self, project_root: str | Path | None = None, python_executable: str | None = None) -> None:
        """初始化执行器，确定项目根目录和 Python 解释器。"""
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.python_executable = python_executable or sys.executable

    def run(self, test_path: str | Path, output_root: str | Path, target_id: str | None = None) -> ExecutionRecord:
        """执行指定测试文件或目录，并生成执行记录。"""
        test_target = Path(test_path)
        workspace = Path(output_root)
        report_dir = workspace / "generated" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_name = f"{test_target.stem}.xml" if test_target.is_file() else "generated-suite.xml"
        report_path = report_dir / report_name
        basetemp_path = workspace / ".pytest_tmp"
        basetemp_path.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        pythonpath_entries = [str(self.project_root), str(workspace)]
        if env.get("PYTHONPATH"):
            pythonpath_entries.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

        started_at = datetime.now(UTC)
        command = [
            self.python_executable,
            "-m",
            "pytest",
            str(test_target),
            "-v",
            f"--basetemp={basetemp_path}",
            f"--junitxml={report_path}",
        ]
        result = subprocess.run(
            command,
            cwd=self.project_root,
            env=env,
            capture_output=True,
            text=True,
        )
        ended_at = datetime.now(UTC)

        error_summary = (result.stderr or result.stdout).strip()
        if result.returncode == 0:
            result_status = "passed"
            error_summary = ""
        else:
            result_status = "failed"

        resolved_target_id = target_id or ("generated-suite" if test_target.is_dir() else test_target.stem)
        total_count, failed_count, error_count, skipped_count = self._parse_junit_counts(report_path)
        passed_count = max(total_count - failed_count - error_count - skipped_count, 0)

        return ExecutionRecord(
            execution_id=f"exec-{resolved_target_id}",
            target_type="test_case",
            target_id=resolved_target_id,
            execution_level="smoke",
            started_at=started_at,
            ended_at=ended_at,
            result_status=result_status,
            report_path=str(report_path),
            error_summary=error_summary,
            environment="local",
            command=" ".join(command),
            exit_code=result.returncode,
            total_count=total_count,
            passed_count=passed_count,
            failed_count=failed_count,
            error_count=error_count,
            skipped_count=skipped_count,
        )

    @staticmethod
    def _parse_junit_counts(report_path: Path) -> tuple[int, int, int, int]:
        """解析 JUnit XML 报告中的总数、失败数、错误数和跳过数。"""
        if not report_path.exists():
            return 0, 0, 0, 0
        try:
            report_root = ElementTree.parse(report_path).getroot()
        except ElementTree.ParseError:
            return 0, 0, 0, 0

        testsuite = report_root.find("testsuite") if report_root.tag == "testsuites" else report_root
        if testsuite is None:
            return 0, 0, 0, 0

        return (
            int(testsuite.attrib.get("tests", 0)),
            int(testsuite.attrib.get("failures", 0)),
            int(testsuite.attrib.get("errors", 0)),
            int(testsuite.attrib.get("skipped", 0)),
        )
