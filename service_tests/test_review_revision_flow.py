"""V2 审核修订生命周期测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


pytestmark = pytest.mark.django_db


def build_reviewable_payload() -> dict:
    """构造可用于审核修订链路验证的最小场景。"""
    return {
        "case_id": "fc-user-revision-001",
        "case_code": "query_user_profile_for_revision",
        "case_name": "查询用户详情待修订场景",
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


def test_revise_rejected_scenario_persists_revision_record_and_updates_step_payload():
    """TC-V2-SVC-004/INT-003 驳回后的结构化修订应落库并更新步骤原始载荷。"""
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(build_reviewable_payload())
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="rejected",
        reviewer="qa-reviewer",
        review_comment="需要修订名称和用户参数",
    )
    step = scenario.steps.get()

    revised = service.revise_scenario(
        scenario_id=scenario.scenario_id,
        reviser="qa-editor",
        revision_comment="已补充修订内容",
        scenario_patch={
            "scenario_name": "查询用户详情（已修订）",
            "scenario_desc": "修订后的场景说明",
            "steps": [
                {
                    "step_id": step.step_id,
                    "step_name": "查询用户详情（修订）",
                    "request": {
                        "path_params": {
                            "user_id": 2,
                        }
                    },
                    "expected": {
                        "status_code": 200,
                        "extract": {
                            "user_id": "id",
                        },
                    },
                }
            ],
        },
    )

    revised.refresh_from_db()
    step.refresh_from_db()

    assert revised.review_status == "revised"
    assert revised.current_stage == "reviewing"
    assert revised.scenario_name == "查询用户详情（已修订）"
    assert revised.scenario_desc == "修订后的场景说明"
    assert revised.revisions.count() == 1
    assert revised.reviews.count() == 2
    assert revised.reviews.order_by("-reviewed_at", "-id").first().review_status == "revised"
    assert step.step_name == "查询用户详情（修订）"
    assert step.metadata["raw_step"]["request"]["path_params"]["user_id"] == 2
    assert step.metadata["raw_step"]["expected"]["extract"]["user_id"] == "id"
    assert step.expected_bindings == ["status_code", "extract"]


def test_revise_endpoint_supports_rejected_to_approved_execution_flow(tmp_path):
    """TC-V2-INT-003 驳回后修订再确认的生命周期闭环应成立。"""
    client = APIClient()
    import_response = client.post("/api/v2/scenarios/import-functional-case/", build_reviewable_payload(), format="json")
    assert import_response.status_code == 201
    scenario_id = import_response.json()["data"]["scenario_id"]

    reject_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "rejected", "reviewer": "qa-reviewer", "review_comment": "先驳回后修订"},
        format="json",
    )
    assert reject_response.status_code == 200

    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")
    assert detail_response.status_code == 200
    step_id = detail_response.json()["data"]["steps"][0]["step_id"]

    revise_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/revise/",
        {
            "reviser": "qa-editor",
            "revision_comment": "补充结构化修订",
            "scenario_name": "查询用户详情（修订后再确认）",
            "steps": [
                {
                    "step_id": step_id,
                    "expected": {
                        "status_code": 200,
                        "extract": {
                            "user_id": "id",
                        },
                    },
                }
            ],
        },
        format="json",
    )
    assert revise_response.status_code == 200
    assert revise_response.json()["data"]["review_status"] == "revised"

    approve_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "修订后通过"},
        format="json",
    )
    assert approve_response.status_code == 200

    execute_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/execute/",
        {"workspace_root": str(tmp_path / "scenario_workspace")},
        format="json",
    )
    assert execute_response.status_code == 202

    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")
    assert result_response.status_code == 200
    assert result_response.json()["data"]["review_status"] == "approved"
    assert result_response.json()["data"]["execution_status"] == "passed"

    detail_after_revision = client.get(f"/api/v2/scenarios/{scenario_id}/")
    assert detail_after_revision.status_code == 200
    detail_data = detail_after_revision.json()["data"]
    assert len(detail_data["revisions"]) == 1
    assert [item["review_status"] for item in detail_data["reviews"]] == ["rejected", "revised", "approved"]


def test_revise_service_blocks_non_rejected_scenario_from_structured_revision():
    """已确认场景未回到待修订状态前不应允许直接进入结构化修订。"""
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(build_reviewable_payload())

    with pytest.raises(ScenarioServiceError, match="当前场景状态不允许直接修订"):
        service.revise_scenario(
            scenario_id=scenario.scenario_id,
            reviser="qa-editor",
            revision_comment="不应通过",
            scenario_patch={"scenario_name": "无效修订"},
        )
