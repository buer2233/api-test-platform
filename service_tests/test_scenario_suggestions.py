"""V2 P1 场景建议治理测试。"""

from __future__ import annotations

from rest_framework.test import APIClient

from scenario_service.models import ScenarioRevisionRecord


def test_suggestion_creation_and_apply_flow_requires_revision_record(service_test_token: str):
    """AI 建议在审批后采纳时必须转成标准修订记录。"""
    client = APIClient()
    import_response = client.post(
        "/api/v2/scenarios/import-functional-case/",
        {
            "case_id": f"fc-ai-001-{service_test_token}",
            "case_code": f"ai_suggestion_user_profile_{service_test_token}",
            "case_name": "AI 建议场景",
            "steps": [
                {
                    "step_name": "查询用户详情",
                    "operation_id": "operation-get-user",
                    "expected": {"status_code": 200},
                }
            ],
        },
        format="json",
    )
    assert import_response.status_code == 201
    scenario_id = import_response.json()["data"]["scenario_id"]

    create_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/",
        {"requester": "qa-owner", "suggestion_type": "assertion_completion"},
        format="json",
    )
    assert create_response.status_code == 201
    suggestion_id = create_response.json()["data"][0]["suggestion_id"]

    list_response = client.get(f"/api/v2/scenarios/{scenario_id}/suggestions/")
    approve_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/{suggestion_id}/approve/",
        {"actor": "qa-owner", "decision_comment": "审批通过"},
        format="json",
    )
    apply_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/{suggestion_id}/apply/",
        {"actor": "qa-owner", "revision_comment": "采纳建议"},
        format="json",
    )
    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")

    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["suggestion_id"] == suggestion_id
    assert list_response.json()["data"][0]["apply_status"] == "pending_approval"

    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["apply_status"] == "approved"
    assert apply_response.status_code == 200
    assert apply_response.json()["data"]["apply_status"] == "adopted"
    assert ScenarioRevisionRecord.objects.filter(scenario__scenario_id=scenario_id).count() == 1
    assert apply_response.json()["data"]["revision_id"].startswith("revision-")

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["review_status"] == "revised"
    assert detail_response.json()["data"]["suggestions"][0]["apply_status"] == "adopted"
