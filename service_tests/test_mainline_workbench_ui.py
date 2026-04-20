"""主工作台前后端分离契约测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


def build_mainline_case_payload(
    *,
    service_test_token: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    module_id: str,
) -> dict:
    """构造主工作台导航树测试使用的功能用例载荷。"""
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "module_id": module_id,
        "case_id": f"fc-mainline-{service_test_token}",
        "case_code": f"mainline_case_{service_test_token}",
        "case_name": "主工作台导航树场景",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def test_mainline_workbench_bootstrap_exposes_vue_design_and_entry_contract():
    """主工作台 bootstrap 应暴露 Vue 前端和 DESIGN.md 入口元数据。"""
    client = APIClient()

    response = client.get("/api/v2/workbench/bootstrap/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["page_title"] == "抓包与接口自动化工作台"
    assert data["frontend_framework"] == "vue3"
    assert data["frontend_entry"] == "/ui/v3/workbench/"
    assert data["design_source"] == "DESIGN.md"


def test_submodule_defaults_to_testcase_list_not_method_list(service_test_token: str):
    """子模块节点应优先暴露测试用例列表，并将测试接口作为并列次级目录。"""
    client = APIClient()
    project_code = f"mainline-project-{service_test_token}"
    environment_code = f"mainline-env-{service_test_token}"
    scenario_set_code = f"mainline-submodule-{service_test_token}"
    module_id = f"account_center_{service_test_token}"
    payload = build_mainline_case_payload(
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        module_id=module_id,
    )

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    navigation_response = client.get("/api/v2/workbench/navigation/")

    assert import_response.status_code == 201
    assert navigation_response.status_code == 200
    projects = navigation_response.json()["data"]["projects"]
    project = next(item for item in projects if item["project_code"] == project_code)
    module = next(item for item in project["modules"] if item["module_code"] == module_id)
    submodule = next(item for item in module["submodules"] if item["submodule_code"] == scenario_set_code)

    assert submodule["testcases"][0]["scenario_name"] == "主工作台导航树场景"
    assert "test_interfaces" in submodule
    assert any(item["method_name"] == "get_user" for item in submodule["test_interfaces"])


def test_theme_switcher_exposes_dark_light_gray_without_layout_variation():
    """主题配置应继续保持三主题，并由前端自行控制布局不变。"""
    client = APIClient()

    response = client.get("/api/v2/scenarios/governance/theme-preference/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    options = payload["data"]["theme_options"]
    assert [item["theme_code"] for item in options] == ["dark", "light", "gray"]


def test_workbench_exposes_allure_report_entry_and_retry_action(service_test_token: str):
    """结果接口应继续为前端暴露报告入口和失败重试状态。"""
    client = APIClient()
    payload = build_mainline_case_payload(
        service_test_token=service_test_token,
        project_code=f"result-project-{service_test_token}",
        environment_code=f"result-env-{service_test_token}",
        scenario_set_code=f"result-submodule-{service_test_token}",
        module_id=f"result_module_{service_test_token}",
    )

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")

    assert import_response.status_code == 201
    scenario_id = import_response.json()["data"]["scenario_id"]
    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")

    assert result_response.status_code == 200
    data = result_response.json()["data"]
    assert "latest_allure_report_path" in data
    assert "retry_available" in data
