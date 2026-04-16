"""V3 P1 G3 Web 正式入口与 Windows Demo 测试。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from rest_framework.test import APIClient


def test_v3_workbench_renders_permission_audit_formalization_and_windows_demo_regions():
    """TC-V3-P1-UI-001 Web 正式入口应承接权限、审计、抓包正式确认和 Windows Demo 区域。"""
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "V3 场景工作台" in content
    assert 'data-testid="actor-panel"' in content
    assert 'data-testid="access-grant-panel"' in content
    assert 'data-testid="audit-log-panel"' in content
    assert 'data-testid="traffic-capture-formalization-panel"' in content
    assert 'data-testid="windows-demo-panel"' in content
    assert "/api/v2/scenarios/governance/access-grants/" in content
    assert "/api/v2/scenarios/governance/audit-logs/" in content
    assert "/api/v2/scenarios/governance/windows-demo/" in content
    assert "/api/v2/scenarios/" in content
    assert "traffic_capture_formalization" in content


def test_windows_demo_manifest_endpoint_returns_browser_first_shared_contract():
    """TC-V3-P1-MIG-002/UI-002 Windows Demo manifest 应与浏览器入口共用同一契约。"""
    client = APIClient()

    response = client.get("/api/v2/scenarios/governance/windows-demo/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["entry_path"] == "/ui/v3/workbench/"
    assert data["preferred_shell"] == "browser_app"
    assert data["tauri_priority"] is True
    assert data["packaging_strategy"] == "browser_first_stage_packaging_recheck"
    assert data["entry_url"].endswith("/ui/v3/workbench/")
    assert "/api/v2/scenarios/" in data["shared_contract_endpoints"]
    assert "/api/v2/scenarios/governance/access-grants/" in data["shared_contract_endpoints"]
    assert "/api/v2/scenarios/governance/audit-logs/" in data["shared_contract_endpoints"]


def test_windows_demo_launcher_dry_run_outputs_v3_entry_url():
    """TC-V3-P1-UI-003/INT-002 Windows 启动器 dry-run 应输出浏览器先验入口命令。"""
    script_path = Path(__file__).resolve().parents[1] / "windows_demo" / "launch_v3_workbench_demo.ps1"

    result = subprocess.run(
        [
            "powershell",
            "-NoLogo",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-BaseUrl",
            "http://127.0.0.1:18080",
            "-SkipServiceStartup",
            "-DryRun",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["entry_url"] == "http://127.0.0.1:18080/ui/v3/workbench/"
    assert payload["launch_mode"] == "browser_first"
    assert payload["browser_mode"] == "app"
    assert payload["tauri_priority"] is True
    assert payload["service_startup_mode"] == "skipped"
