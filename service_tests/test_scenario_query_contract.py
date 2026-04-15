"""V2 P1 查询契约增强测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


DEFAULT_PROJECT_CODE = "default-project"
DEFAULT_ENVIRONMENT_CODE = "default-env"


def build_minimal_capture_payload() -> dict:
    """构造用于筛选查询测试的最小抓包载荷。"""
    return {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-04-10T08:00:00.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://cdn.example.com/assets/app.js",
                    },
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/javascript"},
                    },
                },
                {
                    "startedDateTime": "2026-04-10T08:00:01.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/v1/users/1",
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": "{\"id\":1,\"name\":\"Alice\"}",
                        },
                    },
                },
            ]
        }
    }


def test_list_and_result_contract_support_filters_history_and_diff(tmp_path, service_test_token: str):
    """列表和结果接口应支持筛选、历史和差异摘要。"""
    client = APIClient()
    project_code = f"default-project-{service_test_token}"
    environment_code = f"default-env-{service_test_token}"
    scenario_set_code = f"default-scenario-set-{service_test_token}"
    case_id = f"fc-query-001-{service_test_token}"
    case_code = f"query_contract_user_profile_{service_test_token}"
    payload = {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": case_id,
        "case_code": case_code,
        "case_name": "查询契约场景",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    assert import_response.status_code == 201
    scenario_id = import_response.json()["data"]["scenario_id"]

    review_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "通过"},
        format="json",
    )
    assert review_response.status_code == 200

    execute_first_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/execute/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "workspace_root": str(tmp_path / "run-1"),
        },
        format="json",
    )
    assert execute_first_response.status_code == 202

    execute_second_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/execute/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "workspace_root": str(tmp_path / "run-2"),
        },
        format="json",
    )
    assert execute_second_response.status_code == 202

    capture_response = client.post(
        "/api/v2/scenarios/import-traffic-capture/",
        {
            "capture_name": f"筛选查询抓包样例-{service_test_token}",
            "capture_payload": build_minimal_capture_payload(),
        },
        format="json",
    )
    assert capture_response.status_code == 201

    list_response = client.get(
        "/api/v2/scenarios/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "scenario_set_code": scenario_set_code,
            "source_type": "functional_case",
            "review_status": "approved",
            "ordering": "updated_desc",
        },
    )
    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")
    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")

    assert list_response.status_code == 200
    list_data = list_response.json()["data"]
    assert len(list_data) == 1
    assert list_data[0]["scenario_id"] == scenario_id
    assert list_data[0]["source_summary"]["functional_case"] == 1
    assert list_data[0]["issue_codes"] == []

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["source_summary"]["functional_case"] == 1

    assert result_response.status_code == 200
    result_data = result_response.json()["data"]
    assert len(result_data["execution_history"]) == 2
    assert result_data["project"]["project_code"] == project_code
    assert result_data["environment"]["environment_code"] == environment_code
    assert result_data["latest_diff_summary"]["status_changed"] is False
    assert "passed_count_delta" in result_data["latest_diff_summary"]
