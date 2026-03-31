from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from platform_core.models import ExecutionRecord


class PytestExecutor:
    """最小 pytest 执行器。"""

    def __init__(self, project_root: str | Path | None = None, python_executable: str | None = None) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.python_executable = python_executable or sys.executable

    def run(self, test_path: str | Path, output_root: str | Path, target_id: str | None = None) -> ExecutionRecord:
        test_target = Path(test_path)
        workspace = Path(output_root)
        report_dir = workspace / "generated" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_name = f"{test_target.stem}.xml" if test_target.is_file() else "generated-suite.xml"
        report_path = report_dir / report_name

        env = os.environ.copy()
        pythonpath_entries = [str(self.project_root), str(workspace)]
        if env.get("PYTHONPATH"):
            pythonpath_entries.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

        started_at = datetime.now(UTC)
        result = subprocess.run(
            [
                self.python_executable,
                "-m",
                "pytest",
                str(test_target),
                "-v",
                f"--junitxml={report_path}",
            ],
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
        )
