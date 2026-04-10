"""V2 P1 场景建议治理测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from scenario_service.models import ScenarioRevisionRecord


pytestmark = pytest.mark.django_db


def test_suggestion_creation_and_apply_flow_requires_revision_record():
    """AI 建议采纳后必须转成标准修订记录。"""
    client = APIClient()
    import_response = client.post(
        "/api/v2/scenarios/import-functional-case/",
        {
            "case_id": "fc-ai-001",
            "case_code": "ai_suggestion_user_profile",
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
    apply_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/{suggestion_id}/apply/",
        {"reviser": "qa-owner", "revision_comment": "采纳建议"},
        format="json",
    )
    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")

    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["suggestion_id"] == suggestion_id

    assert apply_response.status_code == 200
    assert apply_response.json()["data"]["apply_status"] == "applied"
    assert ScenarioRevisionRecord.objects.filter(scenario__scenario_id=scenario_id).count() == 1
    assert apply_response.json()["data"]["revision_id"].startswith("revision-")

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["review_status"] == "revised"
    assert detail_response.json()["data"]["suggestions"][0]["apply_status"] == "applied"
