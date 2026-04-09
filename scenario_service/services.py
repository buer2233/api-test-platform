"""V2 场景服务应用层。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from django.db import transaction

from platform_core.functional_cases import FunctionalCaseDraftParser
from platform_core.scenario_execution import ScenarioExecutionBindingError, ScenarioExecutionPipeline
from platform_core.services import PlatformApplicationService
from scenario_service.models import (
    ScenarioExecutionRecord,
    ScenarioRecord,
    ScenarioReviewRecord,
    ScenarioStepRecord,
)


class ScenarioServiceError(Exception):
    """场景服务层的结构化异常。"""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        """初始化结构化错误。"""
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class FunctionalCaseScenarioService:
    """把功能测试用例草稿接入 Django 持久化层。"""

    def __init__(
        self,
        parser: FunctionalCaseDraftParser | None = None,
        application_service: PlatformApplicationService | None = None,
        scenario_execution_pipeline: ScenarioExecutionPipeline | None = None,
    ) -> None:
        """装配解析器与状态校验能力。"""
        self.parser = parser or FunctionalCaseDraftParser()
        self.application_service = application_service or PlatformApplicationService()
        self.scenario_execution_pipeline = scenario_execution_pipeline or ScenarioExecutionPipeline()

    @transaction.atomic
    def import_functional_case(self, payload: dict) -> ScenarioRecord:
        """导入功能测试用例并持久化为场景草稿。"""
        draft = self.parser.parse_payload(
            raw_case=payload,
            source_name=payload.get("case_code") or payload.get("case_id") or "api_request",
        )
        scenario = ScenarioRecord.objects.create(
            scenario_id=draft.scenario.scenario_id,
            scenario_code=draft.scenario.scenario_code,
            scenario_name=draft.scenario.scenario_name,
            module_id=draft.scenario.module_id,
            scenario_desc=draft.scenario.scenario_desc,
            source_ids=draft.scenario.source_ids,
            priority=draft.scenario.priority,
            review_status=draft.lifecycle.review_status,
            execution_status=draft.lifecycle.execution_status,
            current_stage=draft.lifecycle.current_stage,
            issue_count=len(draft.issues),
            step_count=len(draft.steps),
            workspace_root=None,
            report_path=None,
            latest_execution_id=None,
            passed_count=0,
            failed_count=0,
            skipped_count=0,
            issues=[issue.model_dump() for issue in draft.issues],
            metadata=draft.scenario.metadata,
        )
        ScenarioStepRecord.objects.bulk_create(
            [
                ScenarioStepRecord(
                    scenario=scenario,
                    step_id=step.step_id,
                    step_order=step.step_order,
                    step_name=step.step_name,
                    operation_id=step.operation_id,
                    input_bindings=step.input_bindings,
                    expected_bindings=step.expected_bindings,
                    assertion_ids=step.assertion_ids,
                    retry_policy=step.retry_policy,
                    optional=step.optional,
                    metadata=step.metadata,
                )
                for step in draft.steps
            ]
        )
        return scenario

    def get_scenario_detail(self, scenario_id: str) -> dict:
        """返回场景详情结构。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        return {
            **self.build_scenario_summary(scenario),
            "steps": [
                {
                    "step_id": step.step_id,
                    "step_order": step.step_order,
                    "step_name": step.step_name,
                    "operation_id": step.operation_id,
                    "input_bindings": step.input_bindings,
                    "expected_bindings": step.expected_bindings,
                    "assertion_ids": step.assertion_ids,
                    "optional": step.optional,
                }
                for step in scenario.steps.all().order_by("step_order", "id")
            ],
            "issues": scenario.issues,
            "reviews": [
                {
                    "review_id": review.review_id,
                    "reviewer": review.reviewer,
                    "review_status": review.review_status,
                    "review_comment": review.review_comment,
                    "reviewed_at": review.reviewed_at.isoformat(),
                }
                for review in scenario.reviews.all().order_by("reviewed_at", "id")
            ],
        }

    @transaction.atomic
    def review_scenario(
        self,
        scenario_id: str,
        review_status: str,
        reviewer: str,
        review_comment: str | None = None,
    ) -> ScenarioRecord:
        """执行场景审核并写入留痕记录。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        self.application_service.validate_scenario_transition(
            current_review_status=scenario.review_status,
            target_review_status=review_status,
            current_execution_status=scenario.execution_status,
            target_execution_status=scenario.execution_status,
        )
        scenario.review_status = review_status
        scenario.current_stage = self._derive_stage(
            review_status=review_status,
            execution_status=scenario.execution_status,
        )
        scenario.save(update_fields=["review_status", "current_stage", "updated_at"])
        ScenarioReviewRecord.objects.create(
            scenario=scenario,
            review_id=f"review-{uuid4().hex[:12]}",
            reviewer=reviewer,
            review_comment=review_comment or "",
            review_status=review_status,
            reviewed_at=datetime.now(UTC),
            metadata={},
        )
        return scenario

    @transaction.atomic
    def request_execution(
        self,
        scenario_id: str,
        workspace_root: str | Path | None = None,
    ) -> ScenarioExecutionRecord:
        """执行场景并回写统一结果摘要。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        if scenario.review_status != "approved":
            raise ScenarioServiceError(
                code="scenario_not_approved",
                message="场景未确认，禁止触发正式执行。",
                status_code=400,
            )
        resolved_workspace_root = Path(workspace_root) if workspace_root else self._build_default_workspace_root(scenario)
        try:
            pipeline_result = self.scenario_execution_pipeline.run(
                scenario=scenario,
                steps=list(scenario.steps.all().order_by("step_order", "id")),
                output_root=resolved_workspace_root,
            )
        except ScenarioExecutionBindingError as error:
            raise ScenarioServiceError(
                code="unsupported_public_baseline_operation",
                message=str(error),
                status_code=400,
            ) from error

        failed_count = pipeline_result.execution_record.failed_count + pipeline_result.execution_record.error_count
        execution_status = "passed" if pipeline_result.execution_record.result_status == "passed" else "failed"
        execution = ScenarioExecutionRecord.objects.create(
            scenario=scenario,
            execution_id=pipeline_result.execution_record.execution_id,
            execution_status=execution_status,
            passed_count=pipeline_result.execution_record.passed_count,
            failed_count=failed_count,
            skipped_count=pipeline_result.execution_record.skipped_count,
            report_path=pipeline_result.execution_record.report_path or "",
            failure_summary=pipeline_result.execution_record.error_summary or "",
        )
        scenario.latest_execution_id = execution.execution_id
        scenario.execution_status = execution.execution_status
        scenario.workspace_root = pipeline_result.asset_manifest.workspace_root
        scenario.report_path = execution.report_path
        scenario.passed_count = execution.passed_count
        scenario.failed_count = execution.failed_count
        scenario.skipped_count = execution.skipped_count
        scenario.current_stage = self._derive_stage(
            review_status=scenario.review_status,
            execution_status=scenario.execution_status,
        )
        scenario.save(
            update_fields=[
                "latest_execution_id",
                "execution_status",
                "workspace_root",
                "report_path",
                "passed_count",
                "failed_count",
                "skipped_count",
                "current_stage",
                "updated_at",
            ]
        )
        return execution

    def get_scenario_result(self, scenario_id: str) -> dict:
        """返回统一结果查询摘要。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        execution = scenario.executions.first()
        execution_status = execution.execution_status if execution else scenario.execution_status
        return {
            "scenario_id": scenario.scenario_id,
            "scenario_code": scenario.scenario_code,
            "scenario_name": scenario.scenario_name,
            "review_status": scenario.review_status,
            "execution_status": execution_status,
            "latest_execution_id": execution.execution_id if execution else scenario.latest_execution_id,
            "step_count": scenario.step_count,
            "issue_count": scenario.issue_count,
            "passed_count": execution.passed_count if execution else scenario.passed_count,
            "failed_count": execution.failed_count if execution else scenario.failed_count,
            "skipped_count": execution.skipped_count if execution else scenario.skipped_count,
            "report_path": execution.report_path if execution and execution.report_path else scenario.report_path,
            "failure_summary": execution.failure_summary if execution else "",
        }

    def build_scenario_summary(self, scenario: ScenarioRecord) -> dict:
        """构造统一场景摘要。"""
        return {
            "scenario_id": scenario.scenario_id,
            "scenario_code": scenario.scenario_code,
            "scenario_name": scenario.scenario_name,
            "review_status": scenario.review_status,
            "execution_status": scenario.execution_status,
            "current_stage": scenario.current_stage,
            "step_count": scenario.step_count,
            "issue_count": scenario.issue_count,
            "workspace_root": scenario.workspace_root,
            "report_path": scenario.report_path,
            "latest_execution_id": scenario.latest_execution_id,
            "passed_count": scenario.passed_count,
            "failed_count": scenario.failed_count,
            "skipped_count": scenario.skipped_count,
        }

    @staticmethod
    def _derive_stage(review_status: str, execution_status: str) -> str:
        """根据审核态和执行态推导当前阶段。"""
        if execution_status in {"running"}:
            return "executing"
        if execution_status in {"passed", "failed"}:
            return "finished"
        if review_status == "approved":
            return "confirmed"
        if review_status in {"rejected", "revised"}:
            return "reviewing"
        return "draft"

    @staticmethod
    def _get_scenario(scenario_id: str) -> ScenarioRecord:
        """按场景标识加载场景记录。"""
        try:
            return ScenarioRecord.objects.get(scenario_id=scenario_id)
        except ScenarioRecord.DoesNotExist as error:
            raise ScenarioServiceError(
                code="scenario_not_found",
                message=f"未找到场景: {scenario_id}",
                status_code=404,
            ) from error

    @staticmethod
    def _build_default_workspace_root(scenario: ScenarioRecord) -> Path:
        """为未显式指定路径的执行请求构造默认工作区目录。"""
        return (
            Path(__file__).resolve().parent.parent
            / "report"
            / "scenario_workspaces"
            / f"{scenario.scenario_code}_{uuid4().hex[:8]}"
        )
