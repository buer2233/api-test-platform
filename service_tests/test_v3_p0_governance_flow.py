"""V3 P0 多项目与环境治理服务测试。"""

from __future__ import annotations

from rest_framework.test import APIClient

from scenario_service.governance import GovernanceBootstrapService
from scenario_service.models import (
    BaselineVersionRecord,
    ProjectRecord,
    ScenarioExecutionRecord,
    ScenarioRecord,
    ScenarioSetRecord,
    TestEnvironmentRecord,
)
from scenario_service.services import FunctionalCaseScenarioService


def build_minimal_functional_case_payload(service_test_token: str) -> dict:
    """构造 V3 P0 治理测试使用的最小功能用例载荷。"""
    return {
        "case_id": f"fc-p0-governance-001-{service_test_token}",
        "case_code": f"query_user_profile_{service_test_token}",
        "case_name": "P0 默认项目样例",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def test_import_functional_case_assigns_default_governance_context(service_test_token: str):
    """TC-V3-P0-MODEL-001/002/003/004 默认治理上下文应随导入自动建立。"""
    service = FunctionalCaseScenarioService()

    scenario = service.import_functional_case(build_minimal_functional_case_payload(service_test_token))
    detail = service.get_scenario_detail(scenario.scenario_id)

    assert detail["project"]["project_code"] == "default-project"
    assert detail["environment"]["environment_code"] == "default-env"
    assert detail["scenario_set"]["scenario_set_code"] == "default-scenario-set"
    assert detail["baseline_version"]["version_code"]
    assert detail["baseline_version"]["is_frozen"] is True


def test_governance_context_endpoint_returns_default_project_tree():
    """TC-V3-P0-API-001/002 治理上下文查询应返回默认项目树和迁移状态。"""
    client = APIClient()

    response = client.get("/api/v2/scenarios/governance/context/")

    assert response.status_code == 200
    data = response.json()["data"]
    default_project = next(item for item in data["projects"] if item["project_code"] == "default-project")
    assert default_project["environments"][0]["environment_code"] == "default-env"
    assert default_project["scenario_sets"][0]["scenario_set_code"] == "default-scenario-set"
    assert default_project["scenario_sets"][0]["active_version"]["version_code"]
    assert "migration_status" in data


def test_baseline_version_activation_updates_active_version_context():
    """TC-V3-P0-API-003 激活新基线版本后应更新当前生效版本。"""
    client = APIClient()

    context_response = client.get("/api/v2/scenarios/governance/context/")
    assert context_response.status_code == 200
    default_project = next(
        item
        for item in context_response.json()["data"]["projects"]
        if item["project_code"] == "default-project"
    )
    project_code = default_project["project_code"]
    scenario_set_code = default_project["scenario_sets"][0]["scenario_set_code"]

    activate_response = client.post(
        "/api/v2/scenarios/governance/baseline-versions/activate/",
        {
            "project_code": project_code,
            "scenario_set_code": scenario_set_code,
            "version_code": "baseline-v2",
            "version_name": "默认基线 V2",
        },
        format="json",
    )
    context_after_response = client.get("/api/v2/scenarios/governance/context/")

    assert activate_response.status_code == 200
    assert activate_response.json()["data"]["baseline_version"]["version_code"] == "baseline-v2"
    default_project_after = next(
        item
        for item in context_after_response.json()["data"]["projects"]
        if item["project_code"] == "default-project"
    )
    assert default_project_after["scenario_sets"][0]["active_version"]["version_code"] == "baseline-v2"


def test_governance_bootstrap_is_idempotent_and_backfills_legacy_records(service_test_token: str):
    """TC-V3-P0-MIG-001/002/003 默认项目迁移应回填旧记录且可重复执行。"""
    legacy_scenario_id = f"scenario-legacy-query-user-{service_test_token}"
    legacy_execution_id = f"execution-legacy-query-user-{service_test_token}"
    ScenarioRecord.objects.create(
        scenario_id=legacy_scenario_id,
        scenario_code=f"query_user_profile_{service_test_token}",
        scenario_name="历史场景",
        review_status="approved",
        execution_status="passed",
        current_stage="finished",
        issue_count=0,
        step_count=1,
        source_ids=["source-legacy"],
        issues=[],
        metadata={"source_type": "functional_case"},
    )
    legacy_scenario = ScenarioRecord.objects.get(scenario_id=legacy_scenario_id)
    ScenarioExecutionRecord.objects.create(
        scenario=legacy_scenario,
        execution_id=legacy_execution_id,
        execution_status="passed",
        passed_count=1,
        failed_count=0,
        skipped_count=0,
        report_path="legacy/report.xml",
        workspace_root="legacy/workspace",
        trigger_source="manual",
    )

    governance_service = GovernanceBootstrapService()
    governance_service.ensure_bootstrap()
    governance_service.ensure_bootstrap()
    refreshed = ScenarioRecord.objects.get(scenario_id=legacy_scenario_id)
    execution = ScenarioExecutionRecord.objects.get(execution_id=legacy_execution_id)

    assert ProjectRecord.objects.filter(project_code="default-project").count() == 1
    assert TestEnvironmentRecord.objects.filter(
        project__project_code="default-project",
        environment_code="default-env",
    ).count() == 1
    assert ScenarioSetRecord.objects.filter(
        project__project_code="default-project",
        scenario_set_code="default-scenario-set",
    ).count() == 1
    assert BaselineVersionRecord.objects.filter(
        scenario_set__project__project_code="default-project",
        scenario_set__scenario_set_code="default-scenario-set",
        version_code="baseline-v1",
    ).count() == 1
    assert refreshed.project.project_code == "default-project"
    assert refreshed.environment.environment_code == "default-env"
    assert refreshed.scenario_set.scenario_set_code == "default-scenario-set"
    assert execution.project.project_code == "default-project"
    assert governance_service.get_migration_status_summary()["remaining_unassigned_scenarios"] == 0
    assert governance_service.get_migration_status_summary()["remaining_unassigned_executions"] == 0


def test_migration_status_endpoint_returns_bootstrap_summary():
    """TC-V3-P0-API-002 迁移状态接口应返回可复核摘要。"""
    client = APIClient()

    response = client.get("/api/v2/scenarios/governance/migration-status/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert "remaining_unassigned_scenarios" in data
    assert "remaining_unassigned_executions" in data
