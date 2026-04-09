"""V2 场景执行闭环测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


pytestmark = pytest.mark.django_db


def build_executable_payload() -> dict:
    """构造可在公开基线站点执行的最小场景。"""
    return {
        "case_id": "fc-user-003",
        "case_code": "query_user_and_user_todos",
        "case_name": "查询用户并获取该用户待办列表",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {
                    "path_params": {
                        "user_id": 1,
                    }
                },
                "expected": {
                    "status_code": 200,
                    "extract": {
                        "user_id": "id",
                    },
                },
            },
            {
                "step_name": "查询用户待办",
                "operation_id": "operation-list-user-todos",
                "uses": {
                    "user_id": "$scenario.user_id",
                },
                "expected": {
                    "status_code": 200,
                },
            },
        ],
    }


def test_execute_approved_scenario_exports_workspace_and_persists_passed_result(tmp_path):
    """TC-V2-EXEC-001/005/006 已确认场景执行后应导出工作区并回写结果。"""
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(build_executable_payload())
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="可以执行",
    )

    execution = service.request_execution(
        scenario_id=scenario.scenario_id,
        workspace_root=tmp_path / "scenario_workspace",
    )
    scenario.refresh_from_db()

    workspace_root = Path(scenario.workspace_root or "")
    assert execution.execution_status == "passed"
    assert scenario.execution_status == "passed"
    assert scenario.current_stage == "finished"
    assert scenario.latest_execution_id == execution.execution_id
    assert scenario.passed_count == 1
    assert scenario.failed_count == 0
    assert scenario.skipped_count == 0
    assert workspace_root.exists()
    assert (workspace_root / "generated" / "tests" / "test_query_user_and_user_todos.py").exists()
    assert (workspace_root / "generated" / "records" / "asset_manifest.json").exists()
    assert Path(scenario.report_path or "").exists()
    assert execution.report_path == scenario.report_path


def test_execute_scenario_blocks_unsupported_operation_binding_before_running_pytest(tmp_path):
    """TC-V2-EXEC-004 未绑定可执行公开基线操作的场景应在执行前阻断。"""
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(
        {
            "case_id": "fc-user-004",
            "case_code": "unsupported_operation_binding",
            "case_name": "包含未支持操作绑定的场景",
            "steps": [
                {
                    "step_name": "执行未知操作",
                    "operation_id": "operation-unsupported",
                    "expected": {"status_code": 200},
                }
            ],
        }
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="准备执行",
    )

    with pytest.raises(ScenarioServiceError, match="未绑定可执行的公开基线操作"):
        service.request_execution(
            scenario_id=scenario.scenario_id,
            workspace_root=tmp_path / "scenario_workspace",
        )

    scenario.refresh_from_db()
    assert scenario.execution_status == "not_started"
    assert scenario.workspace_root is None
    assert scenario.executions.count() == 0

