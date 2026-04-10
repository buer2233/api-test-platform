"""V2 可用型入口页面与列表契约测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


def test_scenario_list_endpoint_returns_summaries_for_workbench():
    """TC-V2-UI-001/007 入口页需要稳定的场景摘要列表接口。"""
    client = APIClient()
    payload = {
        "case_id": "fc-ui-001",
        "case_code": "ui_query_user_profile",
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

    list_response = client.get("/api/v2/scenarios/")

    assert list_response.status_code == 200
    assert list_response.json()["success"] is True
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["scenario_code"] == "ui_query_user_profile"


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


def test_workbench_duplicate_functional_case_import_returns_structured_error():
    """TC-V2-UI-001 重复导入默认示例时不应抛出 500。"""
    client = APIClient()
    payload = {
        "case_id": "fc-ui-demo-001",
        "case_code": "ui_console_query_user_profile",
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
