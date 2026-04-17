"""V3 P2 AI 治理边界测试。"""

from __future__ import annotations

from django.apps import apps
import pytest
from rest_framework.test import APIClient

from scenario_service.models import ScenarioAuditLogRecord, ScenarioRevisionRecord
from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


def compact_token(service_test_token: str) -> str:
    """提取较短唯一片段，避免 MySQL 字段长度超限。"""
    parts = service_test_token.split("_")
    return "".join(parts[-2:])[:10]


def build_p2_case_payload(
    *,
    service_test_token: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    case_suffix: str,
) -> dict:
    """构造带治理上下文的 P2 场景载荷。"""
    short_token = compact_token(service_test_token)
    short_suffix = case_suffix.replace("-", "")[:8]
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": f"p2{short_suffix}{short_token}",
        "case_code": f"p2_{short_suffix}_{short_token}",
        "case_name": f"{project_code} AI 治理场景 {short_suffix}",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def import_and_approve_p2_scenario(
    *,
    service: FunctionalCaseScenarioService,
    service_test_token: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    case_suffix: str,
):
    """导入并审核通过一个 P2 测试场景。"""
    scenario = service.import_functional_case(
        build_p2_case_payload(
            service_test_token=service_test_token,
            project_code=project_code,
            environment_code=environment_code,
            scenario_set_code=scenario_set_code,
            case_suffix=case_suffix,
        )
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="P2 治理测试审核通过",
    )
    return scenario


def assign_role(
    *,
    service: FunctionalCaseScenarioService,
    project_code: str,
    subject_name: str,
    role_code: str,
) -> dict:
    """为指定项目写入角色。"""
    return service.assign_project_role(
        project_code=project_code,
        operator="platform-admin",
        subject_name=subject_name,
        role_code=role_code,
    )


def create_ai_suggestion(
    *,
    client: APIClient,
    scenario_id: str,
    requester: str = "qa-owner",
) -> dict:
    """通过接口创建一条 AI 建议并返回首条记录。"""
    create_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/",
        {"requester": requester, "suggestion_type": "assertion_completion"},
        format="json",
    )
    assert create_response.status_code == 201
    return create_response.json()["data"][0]


def test_ai_governance_policy_and_decision_models_capture_structured_contract(service_test_token: str):
    """TC-V3-P2-MODEL-001/002 AI 治理策略与责任链对象应具备结构化表达能力。"""
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p2m-{short_token}"
    environment_code = f"p2e-{short_token}"
    scenario_set_code = f"p2s-{short_token}"
    service.governance_service.resolve_context(
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )
    scenario = import_and_approve_p2_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="model",
    )

    policy = service.ensure_ai_governance_policy(
        project_code=project_code,
        operator="platform-admin",
        scope_type="project",
        scope_ref=project_code,
        suggestion_types=["assertion_completion", "step_patch"],
        approval_mode="manual_review",
        rollback_mode="snapshot_restore",
    )
    suggestion = service.create_suggestions(
        scenario_id=scenario.scenario_id,
        requester="qa-owner",
        suggestion_type="assertion_completion",
    )[0]
    service.approve_suggestion(
        scenario_id=scenario.scenario_id,
        suggestion_id=suggestion["suggestion_id"],
        actor="qa-owner",
        decision_comment="模型测试审批通过",
    )

    policy_model = apps.get_model("scenario_service", "AiGovernancePolicyRecord")
    decision_model = apps.get_model("scenario_service", "AiSuggestionDecisionRecord")
    policy_record = policy_model.objects.get(policy_id=policy["policy_id"])
    decision_record = decision_model.objects.get(suggestion__suggestion_id=suggestion["suggestion_id"])

    assert policy_record.project.project_code == project_code
    assert policy_record.approval_mode == "manual_review"
    assert policy_record.rollback_mode == "snapshot_restore"
    assert "step_patch" in policy_record.suggestion_types
    assert policy_record.auto_execution_enabled is False
    assert decision_record.project.project_code == project_code
    assert decision_record.scenario.scenario_id == scenario.scenario_id
    assert decision_record.decision_type == "approve"
    assert decision_record.actor_name == "qa-owner"


def test_ai_suggestion_query_returns_policy_status_and_project_scoped_contract(service_test_token: str):
    """TC-V3-P2-API-001 AI 建议创建与查询接口应返回稳定治理契约。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p2q-{short_token}"
    environment_code = f"p2e-{short_token}"
    scenario_set_code = f"p2s-{short_token}"
    scenario = import_and_approve_p2_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="query",
    )

    policy_response = client.post(
        "/api/v2/scenarios/governance/ai-policies/",
        {
            "project_code": project_code,
            "operator": "platform-admin",
            "scope_type": "project",
            "scope_ref": project_code,
            "suggestion_types": ["assertion_completion"],
            "approval_mode": "manual_review",
            "rollback_mode": "snapshot_restore",
        },
        format="json",
    )
    create_payload = create_ai_suggestion(client=client, scenario_id=scenario.scenario_id)
    list_response = client.get(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/",
        {"actor": "qa-owner"},
    )

    assert policy_response.status_code == 201
    assert list_response.status_code == 200
    assert create_payload["project_code"] == project_code
    assert create_payload["scenario_id"] == scenario.scenario_id
    assert create_payload["apply_status"] == "pending_approval"
    assert create_payload["approval_required"] is True
    assert create_payload["policy_summary"]["approval_mode"] == "manual_review"
    assert list_response.json()["data"][0]["suggestion_id"] == create_payload["suggestion_id"]


def test_ai_suggestion_requires_manual_approval_before_adopt_and_execution(
    service_test_token: str,
    tmp_path,
):
    """TC-V3-P2-API-002/EXEC-001 未审批建议不得直接采纳，也不得触发 AI 执行。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p2a-{short_token}"
    environment_code = f"p2e-{short_token}"
    scenario_set_code = f"p2s-{short_token}"
    scenario = import_and_approve_p2_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="approve",
    )
    create_payload = create_ai_suggestion(client=client, scenario_id=scenario.scenario_id)
    suggestion_id = create_payload["suggestion_id"]

    adopt_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/adopt/",
        {"actor": "qa-owner", "revision_comment": "未经审批直接采纳"},
        format="json",
    )

    assert adopt_response.status_code == 400
    assert adopt_response.json()["error"]["code"] == "ai_suggestion_not_approved"

    with pytest.raises(ScenarioServiceError) as error:
        service.request_execution(
            scenario_id=scenario.scenario_id,
            project_code=project_code,
            environment_code=environment_code,
            workspace_root=tmp_path / "p2-unapproved-ai",
            operator="qa-owner",
            trigger_source="ai_suggestion",
            suggestion_id=suggestion_id,
        )

    assert error.value.code == "ai_suggestion_approval_required"


def test_ai_reject_does_not_change_formal_fact_and_adopt_rollback_restores_previous_state(
    service_test_token: str,
):
    """TC-V3-P2-INT-002/003 拒绝不污染事实，采纳后回退应恢复治理前状态。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p2r-{short_token}"
    environment_code = f"p2e-{short_token}"
    scenario_set_code = f"p2s-{short_token}"
    scenario = import_and_approve_p2_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="rollback",
    )
    create_payload = create_ai_suggestion(client=client, scenario_id=scenario.scenario_id)
    rejected_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{create_payload['suggestion_id']}/reject/",
        {"actor": "qa-owner", "decision_comment": "当前建议不采纳"},
        format="json",
    )
    detail_after_reject = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/")

    assert rejected_response.status_code == 200
    assert rejected_response.json()["data"]["apply_status"] == "rejected"
    assert detail_after_reject.status_code == 200
    assert detail_after_reject.json()["data"]["review_status"] == "approved"
    assert detail_after_reject.json()["data"]["steps"][0]["expected_bindings"] == ["status_code"]

    second_payload = create_ai_suggestion(client=client, scenario_id=scenario.scenario_id)
    suggestion_id = second_payload["suggestion_id"]
    approve_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/approve/",
        {"actor": "qa-owner", "decision_comment": "允许采纳"},
        format="json",
    )
    adopt_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/adopt/",
        {"actor": "qa-owner", "revision_comment": "采纳 AI 建议"},
        format="json",
    )
    detail_after_adopt = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/")
    rollback_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/rollback/",
        {"actor": "qa-owner", "rollback_comment": "回退 AI 采纳结果"},
        format="json",
    )
    detail_after_rollback = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/")

    assert approve_response.status_code == 200
    assert adopt_response.status_code == 200
    assert adopt_response.json()["data"]["apply_status"] == "adopted"
    assert detail_after_adopt.json()["data"]["review_status"] == "revised"
    assert "extract" in detail_after_adopt.json()["data"]["steps"][0]["expected_bindings"]
    assert rollback_response.status_code == 200
    assert rollback_response.json()["data"]["apply_status"] == "rolled_back"
    assert detail_after_rollback.json()["data"]["review_status"] == "approved"
    assert detail_after_rollback.json()["data"]["steps"][0]["expected_bindings"] == ["status_code"]
    assert ScenarioRevisionRecord.objects.filter(scenario__scenario_id=scenario.scenario_id).count() == 1


def test_ai_governance_respects_project_and_role_boundaries(service_test_token: str):
    """TC-V3-P2-ISO-001/002 AI 建议查询、审批和采纳必须受项目与角色边界约束。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p2i-{short_token}"
    environment_code = f"p2e-{short_token}"
    scenario_set_code = f"p2s-{short_token}"
    editor_name = f"editor-{short_token}"
    reviewer_name = f"review-{short_token}"
    outsider_name = f"outsider-{short_token}"
    scenario = import_and_approve_p2_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="isolate",
    )
    assign_role(service=service, project_code=project_code, subject_name=editor_name, role_code="editor")
    assign_role(service=service, project_code=project_code, subject_name=reviewer_name, role_code="reviewer")

    create_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/",
        {"requester": editor_name, "suggestion_type": "assertion_completion"},
        format="json",
    )
    suggestion_id = create_response.json()["data"][0]["suggestion_id"]
    outsider_query_response = client.get(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/",
        {"actor": outsider_name},
    )
    outsider_approve_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/approve/",
        {"actor": outsider_name, "decision_comment": "越权审批"},
        format="json",
    )
    reviewer_approve_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/approve/",
        {"actor": reviewer_name, "decision_comment": "正式审批"},
        format="json",
    )

    assert create_response.status_code == 201
    assert outsider_query_response.status_code == 403
    assert outsider_approve_response.status_code == 403
    assert reviewer_approve_response.status_code == 200
    assert reviewer_approve_response.json()["data"]["apply_status"] == "approved"


def test_ai_governance_audit_chain_is_queryable_after_reject_adopt_and_rollback(service_test_token: str):
    """TC-V3-P2-API-003 审计查询应能还原 AI 建议拒绝、采纳和回退责任链。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p2u-{short_token}"
    environment_code = f"p2e-{short_token}"
    scenario_set_code = f"p2s-{short_token}"
    scenario = import_and_approve_p2_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="audit",
    )
    suggestion = create_ai_suggestion(client=client, scenario_id=scenario.scenario_id)
    suggestion_id = suggestion["suggestion_id"]

    client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/approve/",
        {"actor": "qa-owner", "decision_comment": "审批通过"},
        format="json",
    )
    client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/adopt/",
        {"actor": "qa-owner", "revision_comment": "执行采纳"},
        format="json",
    )
    rollback_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/suggestions/{suggestion_id}/rollback/",
        {"actor": "qa-owner", "rollback_comment": "执行回退"},
        format="json",
    )
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": project_code},
    )

    assert rollback_response.status_code == 200
    assert audit_response.status_code == 200
    audit_logs = audit_response.json()["data"]
    assert any(item["action_type"] == "approve_ai_suggestion" for item in audit_logs)
    assert any(item["action_type"] == "adopt_ai_suggestion" for item in audit_logs)
    assert any(item["action_type"] == "rollback_ai_suggestion" for item in audit_logs)
    assert ScenarioAuditLogRecord.objects.filter(project__project_code=project_code).count() >= 3


def test_v3_workbench_renders_ai_governance_panel_and_status_contract():
    """TC-V3-P2-UI-001 工作台应明确承接 AI 治理状态区与相关接口契约。"""
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="ai-governance-panel"' in content
    assert "AI 治理状态" in content
    assert "/api/v2/scenarios/governance/ai-policies/" in content
    assert "/api/v2/scenarios/" in content
    assert "pending_approval" in content
    assert "rolled_back" in content
