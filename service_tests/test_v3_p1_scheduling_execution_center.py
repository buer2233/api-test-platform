"""V3 P1 G4 调度与执行中心测试。"""

from __future__ import annotations

from django.apps import apps
from rest_framework.test import APIClient

from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


def compact_token(service_test_token: str) -> str:
    """提取较短的唯一片段，避免 MySQL 标识字段过长。"""
    parts = service_test_token.split("_")
    return "".join(parts[-2:])[:10]


def build_schedule_case_payload(
    *,
    service_test_token: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    case_suffix: str,
    operation_id: str,
) -> dict:
    """构造带治理上下文的调度测试场景载荷。"""
    short_token = compact_token(service_test_token)
    short_suffix = case_suffix.replace("-", "")[:8]
    step_request = {"path_params": {"user_id": 1}} if operation_id == "operation-get-user" else {}
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": f"sc{short_suffix}{short_token}",
        "case_code": f"sc_{short_suffix}_{short_token}",
        "case_name": f"{project_code} 调度场景 {short_suffix}",
        "steps": [
            {
                "step_name": "执行公开基线操作",
                "operation_id": operation_id,
                "request": step_request,
                "expected": {"status_code": 200},
            }
        ],
    }


def import_and_approve_schedule_scenario(
    *,
    service: FunctionalCaseScenarioService,
    service_test_token: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    case_suffix: str,
    operation_id: str,
):
    """导入并审核通过一个调度测试场景。"""
    scenario = service.import_functional_case(
        build_schedule_case_payload(
            service_test_token=service_test_token,
            project_code=project_code,
            environment_code=environment_code,
            scenario_set_code=scenario_set_code,
            case_suffix=case_suffix,
            operation_id=operation_id,
        )
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="调度测试审核通过",
    )
    return scenario


def assign_scheduler_role(
    *,
    service: FunctionalCaseScenarioService,
    project_code: str,
    scheduler_name: str,
) -> dict:
    """为指定项目写入 scheduler 角色。"""
    return service.assign_project_role(
        project_code=project_code,
        operator="platform-admin",
        subject_name=scheduler_name,
        role_code="scheduler",
    )


def test_schedule_models_capture_queue_retry_aggregate_and_governance_context(service_test_token: str):
    """TC-V3-P1-MODEL-004 调度对象应能表达任务、队列、重试和聚合摘要。"""
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"p1m-{short_token}"
    environment_code = f"e1m-{short_token}"
    scenario_set_code = f"s1m-{short_token}"
    scheduler_name = f"sch-{short_token}"
    scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="model",
        operation_id="operation-get-user",
    )
    assign_scheduler_role(service=service, project_code=project_code, scheduler_name=scheduler_name)

    batch = service.create_schedule_batch(
        project_code=project_code,
        environment_code=environment_code,
        scheduler=scheduler_name,
        dispatch_strategy="manual_queue",
        scenario_items=[
            {
                "scenario_id": scenario.scenario_id,
                "retry_policy": {"max_retry_count": 2},
            }
        ],
    )

    schedule_batch_model = apps.get_model("scenario_service", "ScenarioScheduleBatchRecord")
    schedule_item_model = apps.get_model("scenario_service", "ScenarioScheduleItemRecord")
    batch_record = schedule_batch_model.objects.get(schedule_batch_id=batch["schedule_batch_id"])
    item_record = schedule_item_model.objects.get(schedule_batch=batch_record)

    assert batch_record.project.project_code == project_code
    assert batch_record.environment.environment_code == environment_code
    assert batch_record.queue_status == "queued"
    assert batch["aggregate_summary"]["queued_count"] == 1
    assert batch["aggregate_summary"]["total_count"] == 1
    assert item_record.item_status == "queued"
    assert item_record.max_retry_count == 2
    assert item_record.retry_count == 0


def test_schedule_center_blocks_cross_project_batch_and_keeps_retry_scoped(
    service_test_token: str,
    tmp_path,
):
    """TC-V3-P1-ISO-003 调度中心的批量执行与重试不得跨项目串扰。"""
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    scheduler_name = f"sch-{short_token}"
    project_a_code = f"pia-{short_token}"
    environment_a_code = f"eia-{short_token}"
    scenario_set_a_code = f"sia-{short_token}"
    project_b_code = f"pib-{short_token}"
    environment_b_code = f"eib-{short_token}"
    scenario_set_b_code = f"sib-{short_token}"
    scenario_a_success = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_a_code,
        environment_code=environment_a_code,
        scenario_set_code=scenario_set_a_code,
        case_suffix="iso-a-success",
        operation_id="operation-get-user",
    )
    scenario_a_failed = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_a_code,
        environment_code=environment_a_code,
        scenario_set_code=scenario_set_a_code,
        case_suffix="iso-a-failed",
        operation_id="operation-unsupported-baseline",
    )
    scenario_b_success = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_b_code,
        environment_code=environment_b_code,
        scenario_set_code=scenario_set_b_code,
        case_suffix="iso-b-success",
        operation_id="operation-get-user",
    )
    assign_scheduler_role(service=service, project_code=project_a_code, scheduler_name=scheduler_name)
    assign_scheduler_role(service=service, project_code=project_b_code, scheduler_name=scheduler_name)

    try:
        service.create_schedule_batch(
            project_code=project_a_code,
            environment_code=environment_a_code,
            scheduler=scheduler_name,
            dispatch_strategy="immediate",
            workspace_root=tmp_path / "mixed-project-batch",
            scenario_items=[
                {"scenario_id": scenario_a_success.scenario_id},
                {"scenario_id": scenario_b_success.scenario_id},
            ],
        )
    except ScenarioServiceError as error:
        assert error.code == "schedule_batch_project_mismatch"
    else:
        raise AssertionError("跨项目调度批次必须被阻断")

    batch_a = service.create_schedule_batch(
        project_code=project_a_code,
        environment_code=environment_a_code,
        scheduler=scheduler_name,
        dispatch_strategy="immediate",
        workspace_root=tmp_path / "project-a-batch",
        scenario_items=[
            {"scenario_id": scenario_a_success.scenario_id},
            {"scenario_id": scenario_a_failed.scenario_id, "retry_policy": {"max_retry_count": 1}},
        ],
    )
    batch_b = service.create_schedule_batch(
        project_code=project_b_code,
        environment_code=environment_b_code,
        scheduler=scheduler_name,
        dispatch_strategy="manual_queue",
        workspace_root=tmp_path / "project-b-batch",
        scenario_items=[
            {"scenario_id": scenario_b_success.scenario_id},
        ],
    )
    failed_item = next(item for item in batch_a["items"] if item["item_status"] == "failed")
    batch_b_before = service.get_schedule_batch_detail(schedule_batch_id=batch_b["schedule_batch_id"], actor=scheduler_name)

    retry_result = service.retry_schedule_item(
        schedule_batch_id=batch_a["schedule_batch_id"],
        schedule_item_id=failed_item["schedule_item_id"],
        scheduler=scheduler_name,
        workspace_root=tmp_path / "project-a-retry",
    )
    batch_b_after = service.get_schedule_batch_detail(schedule_batch_id=batch_b["schedule_batch_id"], actor=scheduler_name)

    assert retry_result["schedule_batch_id"] == batch_a["schedule_batch_id"]
    assert batch_b_before["aggregate_summary"] == batch_b_after["aggregate_summary"]
    assert batch_b_after["items"][0]["item_status"] == "queued"


def test_schedule_batch_api_supports_create_retry_cancel_and_aggregate_query(
    service_test_token: str,
    tmp_path,
):
    """TC-V3-P1-API-004 调度中心接口应支持批量任务创建、重试、取消和结果聚合查询。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"pap-{short_token}"
    environment_code = f"eap-{short_token}"
    scenario_set_code = f"sap-{short_token}"
    scheduler_name = f"sch-{short_token}"
    success_scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="api-success",
        operation_id="operation-get-user",
    )
    failed_scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="api-failed",
        operation_id="operation-unsupported-baseline",
    )
    assign_scheduler_role(service=service, project_code=project_code, scheduler_name=scheduler_name)

    create_response = client.post(
        "/api/v2/scenarios/governance/schedule-batches/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "scheduler": scheduler_name,
            "dispatch_strategy": "immediate",
            "workspace_root": str(tmp_path / "api-batch"),
            "scenario_items": [
                {"scenario_id": success_scenario.scenario_id},
                {"scenario_id": failed_scenario.scenario_id, "retry_policy": {"max_retry_count": 1}},
            ],
        },
        format="json",
    )

    assert create_response.status_code == 201
    batch_payload = create_response.json()["data"]
    failed_item = next(item for item in batch_payload["items"] if item["item_status"] == "failed")
    detail_response = client.get(
        f"/api/v2/scenarios/governance/schedule-batches/{batch_payload['schedule_batch_id']}/",
        {"actor": scheduler_name},
    )
    retry_response = client.post(
        f"/api/v2/scenarios/governance/schedule-batches/{batch_payload['schedule_batch_id']}/items/{failed_item['schedule_item_id']}/retry/",
        {
            "scheduler": scheduler_name,
            "workspace_root": str(tmp_path / "api-batch-retry"),
        },
        format="json",
    )
    queued_response = client.post(
        "/api/v2/scenarios/governance/schedule-batches/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "scheduler": scheduler_name,
            "dispatch_strategy": "manual_queue",
            "scenario_items": [
                {"scenario_id": success_scenario.scenario_id},
            ],
        },
        format="json",
    )
    assert queued_response.status_code == 201
    queued_payload = queued_response.json()["data"]
    queued_item = queued_payload["items"][0]
    cancel_response = client.post(
        f"/api/v2/scenarios/governance/schedule-batches/{queued_payload['schedule_batch_id']}/items/{queued_item['schedule_item_id']}/cancel/",
        {
            "scheduler": scheduler_name,
            "cancel_reason": "人工取消排队任务",
        },
        format="json",
    )
    queued_detail_response = client.get(
        f"/api/v2/scenarios/governance/schedule-batches/{queued_payload['schedule_batch_id']}/",
        {"actor": scheduler_name},
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["aggregate_summary"]["total_count"] == 2
    assert retry_response.status_code == 200
    assert retry_response.json()["data"]["retry_count"] == 1
    assert cancel_response.status_code == 200
    assert cancel_response.json()["data"]["item_status"] == "canceled"
    assert queued_detail_response.status_code == 200
    assert queued_detail_response.json()["data"]["aggregate_summary"]["canceled_count"] == 1


def test_schedule_execution_aggregates_success_failure_retry_and_cancel(
    service_test_token: str,
    tmp_path,
):
    """TC-V3-P1-EXEC-003 批量执行、重试和结果聚合应在项目边界内稳定工作。"""
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"pex-{short_token}"
    environment_code = f"eex-{short_token}"
    scenario_set_code = f"sex-{short_token}"
    scheduler_name = f"sch-{short_token}"
    success_scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="exec-success",
        operation_id="operation-get-user",
    )
    failed_scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="exec-failed",
        operation_id="operation-unsupported-baseline",
    )
    assign_scheduler_role(service=service, project_code=project_code, scheduler_name=scheduler_name)

    batch = service.create_schedule_batch(
        project_code=project_code,
        environment_code=environment_code,
        scheduler=scheduler_name,
        dispatch_strategy="immediate",
        workspace_root=tmp_path / "exec-batch",
        scenario_items=[
            {"scenario_id": success_scenario.scenario_id},
            {"scenario_id": failed_scenario.scenario_id, "retry_policy": {"max_retry_count": 2}},
        ],
    )
    failed_item = next(item for item in batch["items"] if item["item_status"] == "failed")
    retried_item = service.retry_schedule_item(
        schedule_batch_id=batch["schedule_batch_id"],
        schedule_item_id=failed_item["schedule_item_id"],
        scheduler=scheduler_name,
        workspace_root=tmp_path / "exec-retry",
    )
    queued_batch = service.create_schedule_batch(
        project_code=project_code,
        environment_code=environment_code,
        scheduler=scheduler_name,
        dispatch_strategy="manual_queue",
        scenario_items=[
            {"scenario_id": success_scenario.scenario_id},
        ],
    )
    canceled_item = service.cancel_schedule_item(
        schedule_batch_id=queued_batch["schedule_batch_id"],
        schedule_item_id=queued_batch["items"][0]["schedule_item_id"],
        scheduler=scheduler_name,
        cancel_reason="取消等待中的任务",
    )
    batch_detail = service.get_schedule_batch_detail(schedule_batch_id=batch["schedule_batch_id"], actor=scheduler_name)
    queued_detail = service.get_schedule_batch_detail(
        schedule_batch_id=queued_batch["schedule_batch_id"],
        actor=scheduler_name,
    )

    assert batch_detail["aggregate_summary"]["succeeded_count"] == 1
    assert batch_detail["aggregate_summary"]["failed_count"] == 1
    assert batch_detail["aggregate_summary"]["retried_count"] == 1
    assert retried_item["retry_count"] == 1
    assert canceled_item["item_status"] == "canceled"
    assert queued_detail["aggregate_summary"]["canceled_count"] == 1


def test_schedule_center_forms_authorize_execute_retry_aggregate_audit_closure(
    service_test_token: str,
    tmp_path,
):
    """TC-V3-P1-INT-003 调度中心独立验收链路应形成完整闭环。"""
    client = APIClient()
    service = FunctionalCaseScenarioService()
    short_token = compact_token(service_test_token)
    project_code = f"pin-{short_token}"
    environment_code = f"ein-{short_token}"
    scenario_set_code = f"sin-{short_token}"
    scheduler_name = f"sch-{short_token}"
    outsider_name = f"out-{short_token}"
    success_scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="int-success",
        operation_id="operation-get-user",
    )
    failed_scenario = import_and_approve_schedule_scenario(
        service=service,
        service_test_token=service_test_token,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        case_suffix="int-failed",
        operation_id="operation-unsupported-baseline",
    )
    assign_scheduler_role(service=service, project_code=project_code, scheduler_name=scheduler_name)

    blocked_response = client.post(
        "/api/v2/scenarios/governance/schedule-batches/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "scheduler": outsider_name,
            "dispatch_strategy": "immediate",
            "scenario_items": [
                {"scenario_id": success_scenario.scenario_id},
            ],
        },
        format="json",
    )
    create_response = client.post(
        "/api/v2/scenarios/governance/schedule-batches/",
        {
            "project_code": project_code,
            "environment_code": environment_code,
            "scheduler": scheduler_name,
            "dispatch_strategy": "immediate",
            "workspace_root": str(tmp_path / "int-batch"),
            "scenario_items": [
                {"scenario_id": success_scenario.scenario_id},
                {"scenario_id": failed_scenario.scenario_id, "retry_policy": {"max_retry_count": 1}},
            ],
        },
        format="json",
    )

    assert blocked_response.status_code == 403
    assert create_response.status_code == 201
    created_batch = create_response.json()["data"]
    failed_item = next(item for item in created_batch["items"] if item["item_status"] == "failed")
    retry_response = client.post(
        f"/api/v2/scenarios/governance/schedule-batches/{created_batch['schedule_batch_id']}/items/{failed_item['schedule_item_id']}/retry/",
        {
            "scheduler": scheduler_name,
            "workspace_root": str(tmp_path / "int-retry"),
        },
        format="json",
    )
    detail_response = client.get(
        f"/api/v2/scenarios/governance/schedule-batches/{created_batch['schedule_batch_id']}/",
        {"actor": scheduler_name},
    )
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": project_code},
    )

    assert retry_response.status_code == 200
    assert detail_response.status_code == 200
    audit_logs = audit_response.json()["data"]
    assert detail_response.json()["data"]["aggregate_summary"]["total_count"] == 2
    assert any(
        item["action_type"] == "create_schedule_batch"
        and item["actor_name"] == outsider_name
        and item["action_result"] == "blocked"
        for item in audit_logs
    )
    assert any(
        item["action_type"] == "create_schedule_batch"
        and item["actor_name"] == scheduler_name
        and item["action_result"] == "succeeded"
        for item in audit_logs
    )
    assert any(
        item["action_type"] == "retry_schedule_item"
        and item["actor_name"] == scheduler_name
        and item["action_result"] == "succeeded"
        for item in audit_logs
    )


def test_v3_workbench_renders_schedule_center_region():
    """TC-V3-P1-UI-001 补充：Vue 前端入口应继续消费调度中心 API。"""
    client = APIClient()

    entry_response = client.get("/ui/v3/workbench/")
    schedule_response = client.get("/api/v2/scenarios/governance/schedule-batches/")

    assert entry_response.status_code == 200
    assert '<div id="app"></div>' in entry_response.content.decode("utf-8")
    assert schedule_response.status_code == 200
    assert schedule_response.json()["success"] is True
