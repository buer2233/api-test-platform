"""Windows Demo 启动清单构造工具。"""

from __future__ import annotations

from pathlib import Path


WINDOWS_DEMO_ENTRY_PATH = "/ui/v3/workbench/"
WINDOWS_DEMO_LEGACY_ENTRY_PATH = "/ui/v2/workbench/"
WINDOWS_DEMO_LAUNCH_SCRIPT_PATH = Path("windows_demo") / "launch_v3_workbench_demo.ps1"
DEFAULT_WINDOWS_DEMO_BASE_URL = "http://127.0.0.1:18080"
WINDOWS_DEMO_SHARED_CONTRACT_ENDPOINTS = [
    "/api/v2/scenarios/",
    "/api/v2/scenarios/governance/context/",
    "/api/v2/scenarios/governance/ai-policies/",
    "/api/v2/scenarios/governance/access-grants/",
    "/api/v2/scenarios/governance/audit-logs/",
    "/api/v2/scenarios/governance/windows-demo/",
]


def normalize_windows_demo_base_url(base_url: str | None) -> str:
    """规范化 Windows Demo 使用的基础访问地址。"""
    normalized = (base_url or DEFAULT_WINDOWS_DEMO_BASE_URL).strip()
    if not normalized:
        normalized = DEFAULT_WINDOWS_DEMO_BASE_URL
    return normalized.rstrip("/")


def build_windows_demo_manifest(base_url: str | None = None) -> dict:
    """构造 Windows Demo manifest，供 Web 入口与 Windows 启动器共同消费。"""
    resolved_base_url = normalize_windows_demo_base_url(base_url)
    entry_url = f"{resolved_base_url}{WINDOWS_DEMO_ENTRY_PATH}"
    launcher_command = (
        "powershell -NoProfile -ExecutionPolicy Bypass "
        f"-File {WINDOWS_DEMO_LAUNCH_SCRIPT_PATH} -BaseUrl {resolved_base_url}"
    )
    return {
        "demo_id": "v3-workbench-demo",
        "entry_path": WINDOWS_DEMO_ENTRY_PATH,
        "legacy_entry_path": WINDOWS_DEMO_LEGACY_ENTRY_PATH,
        "entry_url": entry_url,
        "preferred_shell": "browser_app",
        "launch_mode": "browser_first",
        "tauri_priority": True,
        "packaging_strategy": "browser_first_stage_packaging_recheck",
        "packaging_status": "browser_app_demo_ready_tauri_pending",
        "launcher_script_path": WINDOWS_DEMO_LAUNCH_SCRIPT_PATH.as_posix(),
        "launcher_command": launcher_command,
        "shared_contract_endpoints": list(WINDOWS_DEMO_SHARED_CONTRACT_ENDPOINTS),
    }
