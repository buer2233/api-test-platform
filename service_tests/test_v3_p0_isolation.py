"""V3 P0 执行隔离与治理边界测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from rest_framework.test import APIClient

from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


def build_project_bound_payload(
    *,
    case_id: str,
    case_code: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
) -> dict:
    """构造带治理上下文的最小功能用例载荷。"""
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": case_id,
        "case_code": case_code,
        "case_name": f"{project_code} 查询用户详情",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def test_same_case_code_can_be_imported_into_different_projects_without_collision(service_test_token: str):
    """TC-V3-P0-ISO-002 同名场景跨项目导入后应保持独立标识和归属。"""
    service = FunctionalCaseScenarioService()
    project_a = f"project-a-{service_test_token}"
    project_b = f"project-b-{service_test_token}"
    environment_a = f"env-a-{service_test_token}"
    environment_b = f"env-b-{service_test_token}"
    scenario_set_a = f"set-a-{service_test_token}"
    scenario_set_b = f"set-b-{service_test_token}"
    case_code = f"query_user_profile_{service_test_token}"

    scenario_a = service.import_functional_case(
        build_project_bound_payload(
            case_id=f"fc-p0-iso-001-{service_test_token}",
            case_code=case_code,
            project_code=project_a,
            environment_code=environment_a,
            scenario_set_code=scenario_set_a,
        )
    )
    scenario_b = service.import_functional_case(
        build_project_bound_payload(
            case_id=f"fc-p0-iso-001-{service_test_token}",
            case_code=case_code,
            project_code=project_b,
            environment_code=environment_b,
            scenario_set_code=scenario_set_b,
        )
    )

    assert scenario_a.scenario_id != scenario_b.scenario_id
    assert scenario_a.project.project_code == project_a
    assert scenario_b.project.project_code == project_b


def test_execution_requires_explicit_project_and_environment_context(tmp_path, service_test_token: str):
    """TC-V3-P0-EXEC-001 缺少项目或环境上下文的执行请求必须被阻断。"""
    service = FunctionalCaseScenarioService()
    project_code = f"project-a-{service_test_token}"
    environment_code = f"env-a-{service_test_token}"
    scenario_set_code = f"set-a-{service_test_token}"
    scenario = service.import_functional_case(
        build_project_bound_payload(
            case_id=f"fc-p0-iso-002-{service_test_token}",
            case_code=f"query_user_profile_{service_test_token}",
            project_code=project_code,
            environment_code=environment_code,
            scenario_set_code=scenario_set_code,
        )
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="通过",
    )

    with pytest.raises(ScenarioServiceError) as error_info:
        service.request_execution(scenario_id=scenario.scenario_id, workspace_root=tmp_path / "run-a")

    assert error_info.value.code == "governance_context_required"


def test_project_scoped_execution_writes_isolated_workspace_and_context_fields(tmp_path, service_test_token: str):
    """TC-V3-P0-ISO-001/004/EXEC-002 执行结果应写回项目和环境隔离上下文。"""
    service = FunctionalCaseScenarioService()
    project_a = f"project-a-{service_test_token}"
    project_b = f"project-b-{service_test_token}"
    environment_a = f"env-a-{service_test_token}"
    environment_b = f"env-b-{service_test_token}"
    scenario_set_a = f"set-a-{service_test_token}"
    scenario_set_b = f"set-b-{service_test_token}"
    case_code = f"query_user_profile_{service_test_token}"

    scenario_a = service.import_functional_case(
        build_project_bound_payload(
            case_id=f"fc-p0-iso-003-{service_test_token}",
            case_code=case_code,
            project_code=project_a,
            environment_code=environment_a,
            scenario_set_code=scenario_set_a,
        )
    )
    scenario_b = service.import_functional_case(
        build_project_bound_payload(
            case_id=f"fc-p0-iso-003-{service_test_token}",
            case_code=case_code,
            project_code=project_b,
            environment_code=environment_b,
            scenario_set_code=scenario_set_b,
        )
    )
    service.review_scenario(scenario_a.scenario_id, "approved", "qa-owner", "通过")
    service.review_scenario(scenario_b.scenario_id, "approved", "qa-owner", "通过")

    execution_a = service.request_execution(
        scenario_id=scenario_a.scenario_id,
        project_code=project_a,
        environment_code=environment_a,
        workspace_root=tmp_path / "project-a-run",
    )
    execution_b = service.request_execution(
        scenario_id=scenario_b.scenario_id,
        project_code=project_b,
        environment_code=environment_b,
        workspace_root=tmp_path / "project-b-run",
    )
    result_a = service.get_scenario_result(scenario_a.scenario_id)
    result_b = service.get_scenario_result(scenario_b.scenario_id)

    assert execution_a.project.project_code == project_a
    assert execution_b.project.project_code == project_b
    assert execution_a.environment.environment_code == environment_a
    assert execution_b.environment.environment_code == environment_b
    assert execution_a.workspace_root != execution_b.workspace_root
    assert Path(execution_a.workspace_root).exists()
    assert Path(execution_b.workspace_root).exists()
    assert result_a["project"]["project_code"] == project_a
    assert result_b["project"]["project_code"] == project_b
    assert result_a["environment"]["environment_code"] == environment_a
    assert result_b["environment"]["environment_code"] == environment_b


def test_export_endpoint_scopes_bundle_path_by_project_and_blocks_cross_project_access(tmp_path, service_test_token: str):
    """TC-V3-P0-ISO-003 导出接口必须按项目归属隔离导出路径和访问边界。"""
    client = APIClient()
    project_a = f"project-a-{service_test_token}"
    project_b = f"project-b-{service_test_token}"
    environment_a = f"env-a-{service_test_token}"
    scenario_set_a = f"set-a-{service_test_token}"
    import_response = client.post(
        "/api/v2/scenarios/import-functional-case/",
        build_project_bound_payload(
            case_id=f"fc-p0-iso-004-{service_test_token}",
            case_code=f"query_user_profile_{service_test_token}",
            project_code=project_a,
            environment_code=environment_a,
            scenario_set_code=scenario_set_a,
        ),
        format="json",
    )
    assert import_response.status_code == 201

    scenario_id = import_response.json()["data"]["scenario_id"]
    export_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/export/",
        {
            "project_code": project_a,
            "export_root": str(tmp_path / "exports"),
        },
        format="json",
    )

    assert export_response.status_code == 200
    data = export_response.json()["data"]
    assert data["project"]["project_code"] == project_a
    assert project_a in data["export_path"]
    assert Path(data["export_path"]).exists()

    blocked_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/export/",
        {
            "project_code": project_b,
            "export_root": str(tmp_path / "exports"),
        },
        format="json",
    )
    assert blocked_response.status_code == 400
    assert blocked_response.json()["error"]["code"] == "project_context_mismatch"
