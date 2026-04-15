"""V2 可用型入口页面与列表契约测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


def test_scenario_list_endpoint_returns_summaries_for_workbench(service_test_token: str):
    """TC-V2-UI-001/007 入口页需要稳定的场景摘要列表接口。"""
    client = APIClient()
    project_code = f"default-project-{service_test_token}"
    environment_code = f"default-env-{service_test_token}"
    scenario_set_code = f"default-scenario-set-{service_test_token}"
    case_id = f"fc-ui-001-{service_test_token}"
    case_code = f"ui_query_user_profile_{service_test_token}"
    payload = {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": case_id,
        "case_code": case_code,
        "case_name": "入口页列表场景",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "expected": {"status_code": 200},
            }
        ],
    }

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    assert import_response.status_code == 201
    scenario_id = import_response.json()["data"]["scenario_id"]

    list_response = client.get(
        "/api/v2/scenarios/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "scenario_set_code": scenario_set_code,
        },
    )

    assert list_response.status_code == 200
    assert list_response.json()["success"] is True
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["scenario_id"] == scenario_id
    assert list_response.json()["data"][0]["scenario_code"] == case_code


def test_workbench_page_renders_import_preview_and_result_regions():
    """TC-V2-UI-001/003/007 可用型入口页应具备导入、预览和结果区域。"""
    client = APIClient()

    response = client.get("/ui/v2/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="workbench-root"' in content
    assert 'data-testid="functional-case-import"' in content
    assert 'data-testid="traffic-capture-import"' in content
    assert 'data-testid="scenario-preview"' in content
    assert 'data-testid="execution-result"' in content
    assert "/api/v2/scenarios/import-functional-case/" in content
    assert "/api/v2/scenarios/import-traffic-capture/" in content


def test_workbench_renders_filter_history_diff_and_suggestion_regions():
    """工作台应展示筛选、历史、差异和建议区域。"""
    client = APIClient()

    response = client.get("/ui/v2/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="scenario-filter-panel"' in content
    assert 'data-testid="execution-history-panel"' in content
    assert 'data-testid="diff-summary-panel"' in content
    assert 'data-testid="suggestion-panel"' in content
    assert "source_type" in content
    assert "issue_code" in content
    assert "suggestions" in content


def test_workbench_duplicate_functional_case_import_returns_structured_error(service_test_token: str):
    """TC-V2-UI-001 重复导入默认示例时不应抛出 500。"""
    client = APIClient()
    payload = {
        "case_id": f"fc-ui-demo-001-{service_test_token}",
        "case_code": f"ui_console_query_user_profile_{service_test_token}",
        "case_name": "入口页示例：查询用户详情",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }

    first_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    duplicate_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 400
    assert duplicate_response.json() == {
        "success": False,
        "error": {
            "code": "scenario_already_exists",
            "message": "场景已存在，请修改场景标识后再导入。",
        },
    }
