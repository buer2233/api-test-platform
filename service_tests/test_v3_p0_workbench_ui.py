"""V3 P0 最小治理入口测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


def build_ui_payload(
    *,
    case_id: str,
    case_code: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
) -> dict:
    """构造治理入口测试使用的导入载荷。"""
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": case_id,
        "case_code": case_code,
        "case_name": f"{project_code} 入口场景",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def test_scenario_list_endpoint_supports_project_environment_and_scenario_set_filters(service_test_token: str):
    """TC-V3-P0-API-001/ISO-002 列表接口应支持治理上下文过滤。"""
    client = APIClient()
    project_a = f"project-a-{service_test_token}"
    project_b = f"project-b-{service_test_token}"
    environment_a = f"env-a-{service_test_token}"
    environment_b = f"env-b-{service_test_token}"
    scenario_set_a = f"set-a-{service_test_token}"
    scenario_set_b = f"set-b-{service_test_token}"
    payload_a = build_ui_payload(
        case_id=f"fc-p0-ui-001-{service_test_token}",
        case_code=f"query_user_profile_{service_test_token}",
        project_code=project_a,
        environment_code=environment_a,
        scenario_set_code=scenario_set_a,
    )
    payload_b = build_ui_payload(
        case_id=f"fc-p0-ui-002-{service_test_token}",
        case_code=f"query_user_profile_other_{service_test_token}",
        project_code=project_b,
        environment_code=environment_b,
        scenario_set_code=scenario_set_b,
    )

    import_a = client.post("/api/v2/scenarios/import-functional-case/", payload_a, format="json")
    import_b = client.post("/api/v2/scenarios/import-functional-case/", payload_b, format="json")
    response = client.get(
        "/api/v2/scenarios/",
        {
            "project_code": project_a,
            "environment_code": environment_a,
            "scenario_set_code": scenario_set_a,
        },
    )

    assert import_a.status_code == 201
    assert import_b.status_code == 201
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["project"]["project_code"] == project_a
    assert data[0]["environment"]["environment_code"] == environment_a
    assert data[0]["scenario_set"]["scenario_set_code"] == scenario_set_a


def test_p0_workbench_renders_governance_switchers_and_context_panels():
    """TC-V3-P0-UI-001/002 最小治理入口应渲染治理切换和上下文区域。"""
    client = APIClient()

    response = client.get("/ui/v2/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="governance-summary"' in content
    assert 'data-testid="project-switcher"' in content
    assert 'data-testid="environment-switcher"' in content
    assert 'data-testid="scenario-set-switcher"' in content
    assert 'data-testid="baseline-version-panel"' in content
    assert "/api/v2/scenarios/governance/context/" in content
    assert "project_code" in content
    assert "environment_code" in content
    assert "scenario_set_code" in content
