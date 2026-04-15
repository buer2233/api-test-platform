"""V3 P1 权限与审计治理测试。"""

from __future__ import annotations

from rest_framework.test import APIClient

from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


def build_project_bound_payload(
    *,
    service_test_token: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    case_suffix: str,
) -> dict:
    """构造带治理上下文的最小功能用例载荷。"""
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": f"fc-p1-auth-{case_suffix}-{service_test_token}",
        "case_code": f"query_user_profile_{case_suffix}_{service_test_token}",
        "case_name": f"{project_code} 权限测试场景",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def test_service_role_assignment_and_blocked_review_attempt_write_audit_logs(service_test_token: str):
    """TC-V3-P1-MODEL-001/002 项目角色授权与越权审核阻断应形成审计留痕。"""
    service = FunctionalCaseScenarioService()
    project_code = f"project-p1-auth-{service_test_token}"
    environment_code = f"env-p1-auth-{service_test_token}"
    scenario_set_code = f"set-p1-auth-{service_test_token}"
    viewer_name = f"qa_viewer_{service_test_token}"
    service.governance_service.resolve_context(
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )

    assignment = service.assign_project_role(
        project_code=project_code,
        operator="platform-admin",
        subject_name=viewer_name,
        role_code="viewer",
    )
    assignments = service.list_project_roles(project_code=project_code)
    scenario = service.import_functional_case(
        build_project_bound_payload(
            service_test_token=service_test_token,
            project_code=project_code,
            environment_code=environment_code,
            scenario_set_code=scenario_set_code,
            case_suffix="001",
        )
    )

    assert assignment["project_code"] == project_code
    assert assignment["subject_name"] == viewer_name
    assert assignment["role_code"] == "viewer"
    assert assignment["permissions"]["can_view"] is True
    assert assignment["permissions"]["can_review"] is False
    assert assignments[0]["subject_name"] == viewer_name

    try:
        service.review_scenario(
            scenario_id=scenario.scenario_id,
            review_status="approved",
            reviewer=viewer_name,
            review_comment="越权审核尝试",
        )
    except ScenarioServiceError as error:
        assert error.code == "project_action_forbidden"
    else:
        raise AssertionError("viewer 角色不应具备审核权限")

    audit_logs = service.list_audit_logs(project_code=project_code, action_type="review_scenario")
    assert audit_logs[0]["action_result"] == "blocked"
    assert audit_logs[0]["actor_name"] == viewer_name
    assert audit_logs[0]["target_id"] == scenario.scenario_id


def test_access_grant_and_audit_log_endpoints_return_project_scoped_contract(service_test_token: str):
    """TC-V3-P1-API-001/002 授权管理与审计日志接口应返回稳定契约。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    project_code = f"project-p1-api-{service_test_token}"
    environment_code = f"env-p1-api-{service_test_token}"
    scenario_set_code = f"set-p1-api-{service_test_token}"
    executor_name = f"qa_executor_{service_test_token}"
    service.governance_service.resolve_context(
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )

    grant_response = client.post(
        "/api/v2/scenarios/governance/access-grants/",
        {
            "project_code": project_code,
            "operator": "platform-admin",
            "subject_name": executor_name,
            "role_code": "executor",
        },
        format="json",
    )
    list_response = client.get("/api/v2/scenarios/governance/access-grants/", {"project_code": project_code})
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": project_code, "action_type": "assign_project_role"},
    )

    assert grant_response.status_code == 201
    assert grant_response.json()["data"]["role_code"] == "executor"
    assert grant_response.json()["data"]["permissions"]["can_execute"] is True
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["subject_name"] == executor_name
    assert audit_response.status_code == 200
    assert audit_response.json()["data"][0]["action_type"] == "assign_project_role"
    assert audit_response.json()["data"][0]["action_result"] == "succeeded"


def test_authorized_review_and_execution_succeed_and_detail_view_blocks_unassigned_actor(
    tmp_path,
    service_test_token: str,
):
    """TC-V3-P1-ISO-001/EXEC-002 有权用户可审核执行，无权用户查看会被阻断并留痕。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    project_code = f"project-p1-int-{service_test_token}"
    environment_code = f"env-p1-int-{service_test_token}"
    scenario_set_code = f"set-p1-int-{service_test_token}"
    reviewer_name = f"qa_reviewer_{service_test_token}"
    executor_name = f"qa_executor_{service_test_token}"
    outsider_name = f"qa_outsider_{service_test_token}"
    scenario = service.import_functional_case(
        build_project_bound_payload(
            service_test_token=service_test_token,
            project_code=project_code,
            environment_code=environment_code,
            scenario_set_code=scenario_set_code,
            case_suffix="002",
        )
    )

    for subject_name, role_code in ((reviewer_name, "reviewer"), (executor_name, "executor")):
        grant_response = client.post(
            "/api/v2/scenarios/governance/access-grants/",
            {
                "project_code": project_code,
                "operator": "platform-admin",
                "subject_name": subject_name,
                "role_code": role_code,
            },
            format="json",
        )
        assert grant_response.status_code == 201

    review_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/review/",
        {
            "review_status": "approved",
            "reviewer": reviewer_name,
            "review_comment": "审核通过",
        },
        format="json",
    )
    execute_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/execute/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "operator": executor_name,
            "workspace_root": str(tmp_path / "authorized-run"),
        },
        format="json",
    )
    blocked_detail_response = client.get(
        f"/api/v2/scenarios/{scenario.scenario_id}/",
        {"actor": outsider_name},
    )
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": project_code},
    )

    assert review_response.status_code == 200
    assert review_response.json()["data"]["review_status"] == "approved"
    assert execute_response.status_code == 202
    assert execute_response.json()["data"]["execution_status"] == "passed"
    assert blocked_detail_response.status_code == 403

    audit_logs = audit_response.json()["data"]
    assert any(
        item["action_type"] == "review_scenario"
        and item["actor_name"] == reviewer_name
        and item["action_result"] == "succeeded"
        for item in audit_logs
    )
    assert any(
        item["action_type"] == "execute_scenario"
        and item["actor_name"] == executor_name
        and item["action_result"] == "succeeded"
        for item in audit_logs
    )
    assert any(
        item["action_type"] == "view_scenario"
        and item["actor_name"] == outsider_name
        and item["action_result"] == "blocked"
        for item in audit_logs
    )
