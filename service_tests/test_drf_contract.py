"""V2 DRF 接口契约测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


DEFAULT_PROJECT_CODE = "default-project"
DEFAULT_ENVIRONMENT_CODE = "default-env"


def test_drf_contract_covers_import_detail_review_execute_and_result(tmp_path, service_test_token: str):
    """TC-V2-SVC-011/012 DRF 接口应覆盖导入、详情、审核、执行与结果查询。"""
    client = APIClient()
    case_id = f"fc-user-001-{service_test_token}"
    case_code = f"query_user_profile_{service_test_token}"
    payload = {
        "case_id": case_id,
        "case_code": case_code,
        "case_name": "查询用户详情",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {
                    "path_params": {
                        "user_id": 1,
                    }
                },
                "expected": {"status_code": 200},
            }
        ],
    }

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    assert import_response.status_code == 201

    scenario_id = import_response.json()["data"]["scenario_id"]

    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["scenario_id"] == scenario_id
    assert detail_response.json()["data"]["source_summary"]["functional_case"] == 1
    assert detail_response.json()["data"]["issue_codes"] == []

    review_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "通过"},
        format="json",
    )
    assert review_response.status_code == 200
    assert review_response.json()["data"]["review_status"] == "approved"

    execute_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/execute/",
        {
            "project_code": DEFAULT_PROJECT_CODE,
            "environment_code": DEFAULT_ENVIRONMENT_CODE,
            "workspace_root": str(tmp_path / "scenario_workspace"),
        },
        format="json",
    )
    assert execute_response.status_code == 202

    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")
    assert result_response.status_code == 200
    assert result_response.json()["data"]["review_status"] == "approved"
    assert result_response.json()["data"]["project"]["project_code"] == DEFAULT_PROJECT_CODE
    assert result_response.json()["data"]["environment"]["environment_code"] == DEFAULT_ENVIRONMENT_CODE
    assert "execution_status" in result_response.json()["data"]
    assert len(result_response.json()["data"]["execution_history"]) == 1
    assert "latest_diff_summary" in result_response.json()["data"]


def test_result_summary_returns_report_path_and_statistics_after_execution(tmp_path, service_test_token: str):
    """TC-V2-SVC-012 结果查询接口应返回执行后的报告路径与统计摘要。"""
    client = APIClient()
    case_id = f"fc-user-003-{service_test_token}"
    case_code = f"query_user_and_user_todos_{service_test_token}"
    payload = {
        "case_id": case_id,
        "case_code": case_code,
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

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    assert import_response.status_code == 201
    scenario_id = import_response.json()["data"]["scenario_id"]

    review_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "通过"},
        format="json",
    )
    assert review_response.status_code == 200

    execute_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/execute/",
        {
            "project_code": DEFAULT_PROJECT_CODE,
            "environment_code": DEFAULT_ENVIRONMENT_CODE,
            "workspace_root": str(tmp_path / "scenario_workspace"),
        },
        format="json",
    )
    assert execute_response.status_code == 202

    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")
    assert result_response.status_code == 200
    data = result_response.json()["data"]
    assert data["execution_status"] == "passed"
    assert data["passed_count"] == 1
    assert data["failed_count"] == 0
    assert data["skipped_count"] == 0
    assert data["project"]["project_code"] == DEFAULT_PROJECT_CODE
    assert data["environment"]["environment_code"] == DEFAULT_ENVIRONMENT_CODE
    assert data["report_path"]
    assert len(data["execution_history"]) == 1
    assert data["latest_diff_summary"]["status_changed"] is False


def test_execute_endpoint_blocks_unapproved_scenario_with_structured_error(service_test_token: str):
    """TC-V2-SVC-011 未确认场景的执行接口应返回结构化错误。"""
    client = APIClient()
    case_id = f"fc-user-002-{service_test_token}"
    case_code = f"query_user_profile_without_review_{service_test_token}"
    payload = {
        "case_id": case_id,
        "case_code": case_code,
        "case_name": "未审核直接执行",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "expected": {"status_code": 200},
            }
        ],
    }

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    scenario_id = import_response.json()["data"]["scenario_id"]

    execute_response = client.post(f"/api/v2/scenarios/{scenario_id}/execute/", {}, format="json")

    assert execute_response.status_code == 400
    assert execute_response.json()["success"] is False
    assert execute_response.json()["error"]["code"] == "scenario_not_approved"
