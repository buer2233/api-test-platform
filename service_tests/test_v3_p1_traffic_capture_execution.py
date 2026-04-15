"""V3 P1 抓包正式执行闭环测试。"""

from __future__ import annotations

from rest_framework.test import APIClient

from scenario_service.services import FunctionalCaseScenarioService


def build_formalizable_traffic_capture_payload() -> dict:
    """构造可被正式绑定到公开基线操作的最小抓包载荷。"""
    return {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-04-15T09:00:00.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://jsonplaceholder.typicode.com/users/1",
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": '{"id": 1, "name": "Leanne Graham"}',
                        },
                    },
                },
                {
                    "startedDateTime": "2026-04-15T09:00:01.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://jsonplaceholder.typicode.com/users/1/todos",
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": '[{"userId": 1, "id": 1, "title": "delectus aut autem"}]',
                        },
                    },
                },
            ]
        }
    }


def test_traffic_capture_formalization_tracks_confirmation_binding_and_readiness(service_test_token: str):
    """TC-V3-P1-MODEL-003 抓包正式执行对象应能表达确认、绑定和执行就绪状态。"""
    service = FunctionalCaseScenarioService()
    project_code = f"capture-project-{service_test_token}"
    environment_code = f"capture-env-{service_test_token}"
    scenario_set_code = f"capture-set-{service_test_token}"
    scenario = service.import_traffic_capture(
        capture_name=f"抓包正式执行-{service_test_token}",
        capture_payload=build_formalizable_traffic_capture_payload(),
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="审核通过",
    )

    confirmation = service.confirm_traffic_capture(
        scenario_id=scenario.scenario_id,
        confirmer="qa-owner",
        confirm_comment="允许进入正式绑定阶段",
    )
    steps = list(scenario.steps.all().order_by("step_order", "id"))
    binding_summary = service.confirm_traffic_capture_bindings(
        scenario_id=scenario.scenario_id,
        confirmer="qa-owner",
        step_bindings=[
            {
                "step_id": steps[0].step_id,
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200, "extract": {"user_id": "id"}},
                "uses": {},
            },
            {
                "step_id": steps[1].step_id,
                "operation_id": "operation-list-user-todos",
                "request": {},
                "expected": {"status_code": 200},
                "uses": {"user_id": "$scenario.user_id"},
            },
        ],
        confirm_comment="抓包候选绑定已转正式绑定",
    )
    detail = service.get_scenario_detail(scenario_id=scenario.scenario_id)

    assert confirmation["confirmation_status"] == "confirmed"
    assert confirmation["binding_status"] == "pending"
    assert binding_summary["binding_status"] == "confirmed"
    assert detail["traffic_capture_formalization"]["execution_readiness"] == "ready"
    assert detail["traffic_capture_formalization"]["confirmed_by"] == "qa-owner"
    assert detail["traffic_capture_formalization"]["bindings_confirmed_by"] == "qa-owner"
    assert detail["steps"][0]["operation_id"] == "operation-get-user"
    assert detail["steps"][1]["operation_id"] == "operation-list-user-todos"
    assert detail["issue_codes"] == []


def test_traffic_capture_confirmation_endpoints_form_project_scoped_contract(service_test_token: str):
    """TC-V3-P1-API-003 抓包正式确认与绑定确认接口应返回稳定契约。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    project_code = f"capture-api-project-{service_test_token}"
    environment_code = f"capture-api-env-{service_test_token}"
    scenario_set_code = f"capture-api-set-{service_test_token}"
    scenario = service.import_traffic_capture(
        capture_name=f"抓包接口确认-{service_test_token}",
        capture_payload=build_formalizable_traffic_capture_payload(),
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="审核通过",
    )
    steps = list(scenario.steps.all().order_by("step_order", "id"))

    confirm_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/confirm/",
        {"confirmer": "qa-owner", "confirm_comment": "进入正式绑定阶段"},
        format="json",
    )
    binding_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/bindings/confirm/",
        {
            "confirmer": "qa-owner",
            "confirm_comment": "绑定确认",
            "step_bindings": [
                {
                    "step_id": steps[0].step_id,
                    "operation_id": "operation-get-user",
                    "request": {"path_params": {"user_id": 1}},
                    "expected": {"status_code": 200, "extract": {"user_id": "id"}},
                    "uses": {},
                },
                {
                    "step_id": steps[1].step_id,
                    "operation_id": "operation-list-user-todos",
                    "request": {},
                    "expected": {"status_code": 200},
                    "uses": {"user_id": "$scenario.user_id"},
                },
            ],
        },
        format="json",
    )
    detail_response = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/")

    assert confirm_response.status_code == 200
    assert confirm_response.json()["data"]["confirmation_status"] == "confirmed"
    assert binding_response.status_code == 200
    assert binding_response.json()["data"]["binding_status"] == "confirmed"
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["traffic_capture_formalization"]["execution_readiness"] == "ready"


def test_traffic_capture_execution_requires_formalization_and_writes_traceable_result(
    tmp_path,
    service_test_token: str,
):
    """TC-V3-P1-ISO-002/EXEC-001/INT-001 抓包正式执行应受确认门禁约束并完成结果回写。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    project_code = f"capture-exec-project-{service_test_token}"
    environment_code = f"capture-exec-env-{service_test_token}"
    scenario_set_code = f"capture-exec-set-{service_test_token}"
    scenario = service.import_traffic_capture(
        capture_name=f"抓包执行链路-{service_test_token}",
        capture_payload=build_formalizable_traffic_capture_payload(),
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="审核通过",
    )
    steps = list(scenario.steps.all().order_by("step_order", "id"))

    blocked_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/execute/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "operator": "qa-owner",
            "workspace_root": str(tmp_path / "capture-blocked"),
        },
        format="json",
    )

    client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/confirm/",
        {"confirmer": "qa-owner", "confirm_comment": "进入正式绑定阶段"},
        format="json",
    )
    client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/bindings/confirm/",
        {
            "confirmer": "qa-owner",
            "confirm_comment": "绑定确认",
            "step_bindings": [
                {
                    "step_id": steps[0].step_id,
                    "operation_id": "operation-get-user",
                    "request": {"path_params": {"user_id": 1}},
                    "expected": {"status_code": 200, "extract": {"user_id": "id"}},
                    "uses": {},
                },
                {
                    "step_id": steps[1].step_id,
                    "operation_id": "operation-list-user-todos",
                    "request": {},
                    "expected": {"status_code": 200},
                    "uses": {"user_id": "$scenario.user_id"},
                },
            ],
        },
        format="json",
    )
    execute_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/execute/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "operator": "qa-owner",
            "workspace_root": str(tmp_path / "capture-ready"),
        },
        format="json",
    )
    result_response = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/result/")
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": project_code, "action_type": "confirm_traffic_capture_bindings"},
    )

    assert blocked_response.status_code == 400
    assert blocked_response.json()["error"]["code"] == "traffic_capture_formalization_required"
    assert execute_response.status_code == 202
    assert execute_response.json()["data"]["execution_status"] == "passed"
    assert result_response.status_code == 200
    assert result_response.json()["data"]["execution_status"] == "passed"
    assert result_response.json()["data"]["traffic_capture_formalization"]["last_execution_id"]
    assert len(result_response.json()["data"]["execution_history"]) == 1
    assert audit_response.status_code == 200
    assert audit_response.json()["data"][0]["action_result"] == "succeeded"
