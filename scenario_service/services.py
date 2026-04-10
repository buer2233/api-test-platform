"""V2 场景服务应用层。"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from django.db import transaction

from platform_core.functional_cases import FunctionalCaseDraftParser
from platform_core.models import FunctionalCaseDraft
from platform_core.scenario_execution import ScenarioExecutionBindingError, ScenarioExecutionPipeline
from platform_core.services import PlatformApplicationService
from platform_core.traffic_capture import TrafficCaptureDraftParser
from scenario_service.models import (
    ScenarioExecutionRecord,
    ScenarioRecord,
    ScenarioRevisionRecord,
    ScenarioReviewRecord,
    ScenarioSourceRecord,
    ScenarioSuggestionRecord,
    ScenarioStepRecord,
)
from scenario_service.suggestion_providers import BaseSuggestionProvider, RuleBasedSuggestionProvider


class ScenarioServiceError(Exception):
    """场景服务层的结构化异常。"""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        """初始化结构化错误。"""
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class FunctionalCaseScenarioService:
    """把多来源场景草稿接入 Django 持久化层。"""

    def __init__(
        self,
        parser: FunctionalCaseDraftParser | None = None,
        traffic_capture_parser: TrafficCaptureDraftParser | None = None,
        application_service: PlatformApplicationService | None = None,
        scenario_execution_pipeline: ScenarioExecutionPipeline | None = None,
        suggestion_provider: BaseSuggestionProvider | None = None,
    ) -> None:
        """装配解析器与状态校验能力。"""
        self.parser = parser or FunctionalCaseDraftParser()
        self.traffic_capture_parser = traffic_capture_parser or TrafficCaptureDraftParser()
        self.application_service = application_service or PlatformApplicationService()
        self.scenario_execution_pipeline = scenario_execution_pipeline or ScenarioExecutionPipeline()
        self.suggestion_provider = suggestion_provider or RuleBasedSuggestionProvider()

    @transaction.atomic
    def import_functional_case(self, payload: dict) -> ScenarioRecord:
        """导入功能测试用例并持久化为场景草稿。"""
        draft = self.parser.parse_payload(
            raw_case=payload,
            source_name=payload.get("case_code") or payload.get("case_id") or "api_request",
        )
        return self._persist_scenario_draft(draft=draft)

    @transaction.atomic
    def import_traffic_capture(self, capture_name: str, capture_payload: dict) -> ScenarioRecord:
        """导入抓包数据并持久化为场景草稿。"""
        draft = self.traffic_capture_parser.parse_payload(
            raw_capture=capture_payload,
            source_name=capture_name or "traffic_capture",
        )
        return self._persist_scenario_draft(draft=draft)

    @staticmethod
    def _persist_scenario_draft(draft: FunctionalCaseDraft) -> ScenarioRecord:
        """把统一场景草稿对象持久化为场景与步骤记录。"""
        if ScenarioRecord.objects.filter(scenario_id=draft.scenario.scenario_id).exists():
            raise ScenarioServiceError(
                code="scenario_already_exists",
                message="场景已存在，请修改场景标识后再导入。",
                status_code=400,
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
            metadata={
                **draft.scenario.metadata,
                "source_type": draft.source_document.source_type,
                "source_name": draft.source_document.source_name,
            },
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
        FunctionalCaseScenarioService._persist_source_traces(scenario=scenario, draft=draft)
        return scenario

    @staticmethod
    def _persist_source_traces(scenario: ScenarioRecord, draft: FunctionalCaseDraft) -> None:
        """把场景和步骤的来源事实写入追溯表。"""
        source_records = [
            ScenarioSourceRecord(
                scenario=scenario,
                entity_type="scenario",
                entity_id=scenario.scenario_id,
                source_type=draft.source_document.source_type,
                source_ref=draft.source_document.source_id,
                confidence="high",
                issue_tags=[issue.issue_code for issue in draft.issues],
                metadata={"source_name": draft.source_document.source_name},
            )
        ]
        for step in draft.steps:
            source_trace = ((step.metadata or {}).get("source_traces") or [{}])[0]
            source_records.append(
                ScenarioSourceRecord(
                    scenario=scenario,
                    entity_type="step",
                    entity_id=step.step_id,
                    source_type=source_trace.get("source_type", draft.source_document.source_type),
                    source_ref=source_trace.get("source_ref", draft.source_document.source_id),
                    confidence=source_trace.get("confidence", step.metadata.get("capture_confidence", "high")),
                    issue_tags=source_trace.get("issue_tags", []),
                    metadata={
                        **step.metadata,
                        **source_trace.get("metadata", {}),
                    },
                )
            )
        ScenarioSourceRecord.objects.bulk_create(source_records)

    @staticmethod
    def _build_source_traces(scenario: ScenarioRecord) -> list[dict]:
        """构造场景详情返回使用的来源追溯摘要。"""
        return [
            {
                "entity_type": source.entity_type,
                "entity_id": source.entity_id,
                "source_type": source.source_type,
                "source_ref": source.source_ref,
                "confidence": source.confidence,
                "issue_tags": source.issue_tags,
                "metadata": source.metadata,
            }
            for source in scenario.sources.all().order_by("id")
        ]

    @staticmethod
    def _build_execution_history(scenario: ScenarioRecord) -> list[dict]:
        """构造结果查询使用的执行历史摘要。"""
        return [
            {
                "execution_id": execution.execution_id,
                "execution_status": execution.execution_status,
                "passed_count": execution.passed_count,
                "failed_count": execution.failed_count,
                "skipped_count": execution.skipped_count,
                "report_path": execution.report_path,
                "failure_summary": execution.failure_summary,
                "trigger_source": execution.trigger_source,
                "based_on_revision_id": execution.based_on_revision_id,
                "based_on_suggestion_id": execution.based_on_suggestion_id,
                "change_summary": execution.change_summary,
                "diff_summary": execution.diff_summary,
                "created_at": execution.created_at.isoformat(),
            }
            for execution in scenario.executions.all().order_by("-created_at", "-id")
        ]

    @staticmethod
    def _build_suggestion_records(scenario: ScenarioRecord) -> list[dict]:
        """构造场景详情和建议查询使用的建议记录摘要。"""
        return [
            {
                "suggestion_id": suggestion.suggestion_id,
                "suggestion_type": suggestion.suggestion_type,
                "target_type": suggestion.target_type,
                "target_id": suggestion.target_id,
                "baseline_revision_id": suggestion.baseline_revision_id,
                "patch_payload": suggestion.patch_payload,
                "diff_summary": suggestion.diff_summary,
                "confidence": suggestion.confidence,
                "apply_status": suggestion.apply_status,
                "created_at": suggestion.created_at.isoformat(),
            }
            for suggestion in scenario.suggestions.all().order_by("-created_at", "-id")
        ]

    @staticmethod
    def _build_source_summary(scenario: ScenarioRecord) -> dict[str, int]:
        """按场景级来源记录构造来源类型聚合摘要。"""
        source_summary: dict[str, int] = {}
        for source in scenario.sources.all().order_by("id"):
            if source.entity_type != "scenario":
                continue
            source_summary[source.source_type] = source_summary.get(source.source_type, 0) + 1
        return source_summary

    @staticmethod
    def _build_issue_codes(scenario: ScenarioRecord) -> list[str]:
        """提取场景当前聚合的问题编码列表。"""
        issue_codes: list[str] = []
        for issue in scenario.issues:
            issue_code = issue.get("issue_code")
            if not issue_code or issue_code in issue_codes:
                continue
            issue_codes.append(issue_code)
        return issue_codes

    @staticmethod
    def _build_empty_diff_summary() -> dict:
        """返回无历史对比时使用的默认差异摘要。"""
        return {
            "status_changed": False,
            "passed_count_delta": 0,
            "failed_count_delta": 0,
            "skipped_count_delta": 0,
            "failure_summary_changed": False,
        }

    @classmethod
    def _build_execution_diff_summary(
        cls,
        *,
        execution_status: str,
        passed_count: int,
        failed_count: int,
        skipped_count: int,
        failure_summary: str,
        previous_execution: ScenarioExecutionRecord | None,
    ) -> dict:
        """构造当前执行与上一次执行之间的轻量差异摘要。"""
        if previous_execution is None:
            return cls._build_empty_diff_summary()
        return {
            "status_changed": execution_status != previous_execution.execution_status,
            "passed_count_delta": passed_count - previous_execution.passed_count,
            "failed_count_delta": failed_count - previous_execution.failed_count,
            "skipped_count_delta": skipped_count - previous_execution.skipped_count,
            "failure_summary_changed": failure_summary != (previous_execution.failure_summary or ""),
        }

    @classmethod
    def _build_latest_diff_summary(cls, scenario: ScenarioRecord) -> dict:
        """返回场景最近一次执行的差异摘要。"""
        latest_execution = scenario.executions.first()
        if latest_execution is None:
            return cls._build_empty_diff_summary()
        if latest_execution.diff_summary:
            return latest_execution.diff_summary
        return cls._build_empty_diff_summary()

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
            "revisions": [
                {
                    "revision_id": revision.revision_id,
                    "reviser": revision.reviser,
                    "revision_comment": revision.revision_comment,
                    "applied_changes": revision.applied_changes,
                    "revised_at": revision.revised_at.isoformat(),
                }
                for revision in scenario.revisions.all().order_by("revised_at", "id")
            ],
            "suggestions": self._build_suggestion_records(scenario),
            "source_traces": self._build_source_traces(scenario),
        }

    def list_scenarios(self, filters: dict | None = None) -> list[dict]:
        """按筛选条件返回供入口页消费的场景摘要列表。"""
        filters = filters or {}
        queryset = ScenarioRecord.objects.all()

        source_type = filters.get("source_type")
        if source_type:
            queryset = queryset.filter(sources__source_type=source_type).distinct()

        review_status = filters.get("review_status")
        if review_status:
            queryset = queryset.filter(review_status=review_status)

        execution_status = filters.get("execution_status")
        if execution_status:
            queryset = queryset.filter(execution_status=execution_status)

        ordering = filters.get("ordering", "updated_desc")
        if ordering == "updated_asc":
            queryset = queryset.order_by("updated_at", "id")
        else:
            queryset = queryset.order_by("-updated_at", "-id")

        scenarios = list(queryset)
        issue_code = filters.get("issue_code")
        if issue_code:
            scenarios = [
                scenario
                for scenario in scenarios
                if issue_code in self._build_issue_codes(scenario)
            ]
        return [self.build_scenario_summary(scenario) for scenario in scenarios]

    @transaction.atomic
    def create_suggestions(self, scenario_id: str, requester: str, suggestion_type: str) -> list[dict]:
        """为指定场景生成并持久化建议记录。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        suggestion_payloads = self.suggestion_provider.generate(scenario, suggestion_type)
        if not suggestion_payloads:
            raise ScenarioServiceError(
                code="scenario_suggestion_empty",
                message="当前场景暂无可生成的建议。",
                status_code=400,
            )

        baseline_revision_id = self._get_latest_revision_id(scenario) or ""
        records = [
            ScenarioSuggestionRecord.objects.create(
                scenario=scenario,
                suggestion_id=f"suggestion-{uuid4().hex[:12]}",
                suggestion_type=suggestion_type,
                target_type=payload["target_type"],
                target_id=payload.get("target_id", ""),
                baseline_revision_id=baseline_revision_id,
                patch_payload=payload["patch_payload"],
                diff_summary={
                    **payload.get("diff_summary", {}),
                    "requester": requester,
                },
                confidence=payload.get("confidence", "medium"),
                apply_status="pending",
            )
            for payload in suggestion_payloads
        ]
        return self._build_suggestion_records(scenario)

    def list_suggestions(self, scenario_id: str) -> list[dict]:
        """返回指定场景的建议记录列表。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        return self._build_suggestion_records(scenario)

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
    def revise_scenario(
        self,
        scenario_id: str,
        reviser: str,
        revision_comment: str | None,
        scenario_patch: dict,
    ) -> ScenarioRecord:
        """执行场景结构化修订并写入修订与审核留痕。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        if scenario.review_status not in {"rejected", "revised"}:
            raise ScenarioServiceError(
                code="scenario_revision_not_allowed",
                message="当前场景状态不允许直接修订。",
                status_code=400,
            )
        if scenario.execution_status == "running":
            raise ScenarioServiceError(
                code="scenario_running_cannot_revise",
                message="执行中的场景禁止进入结构化修订。",
                status_code=400,
            )
        return self._apply_revision_patch(
            scenario=scenario,
            reviser=reviser,
            revision_comment=revision_comment or "",
            scenario_patch=scenario_patch,
            suggestion_id=None,
        )

    @transaction.atomic
    def apply_suggestion(
        self,
        scenario_id: str,
        suggestion_id: str,
        reviser: str,
        revision_comment: str | None = None,
    ) -> dict:
        """采纳建议并转成标准修订记录。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        if scenario.execution_status == "running":
            raise ScenarioServiceError(
                code="scenario_running_cannot_apply_suggestion",
                message="执行中的场景禁止采纳建议。",
                status_code=400,
            )
        try:
            suggestion = scenario.suggestions.get(suggestion_id=suggestion_id)
        except ScenarioSuggestionRecord.DoesNotExist as error:
            raise ScenarioServiceError(
                code="scenario_suggestion_not_found",
                message=f"未找到建议: {suggestion_id}",
                status_code=404,
            ) from error

        if suggestion.apply_status == "applied":
            raise ScenarioServiceError(
                code="scenario_suggestion_already_applied",
                message="该建议已采纳，无需重复处理。",
                status_code=400,
            )

        patched_scenario = self._apply_revision_patch(
            scenario=scenario,
            reviser=reviser,
            revision_comment=revision_comment or "采纳建议",
            scenario_patch=suggestion.patch_payload,
            suggestion_id=suggestion.suggestion_id,
        )
        latest_revision = patched_scenario.revisions.order_by("-revised_at", "-id").first()
        suggestion.apply_status = "applied"
        suggestion.save(update_fields=["apply_status", "updated_at"])
        return {
            "suggestion_id": suggestion.suggestion_id,
            "apply_status": suggestion.apply_status,
            "revision_id": latest_revision.revision_id if latest_revision else "",
        }

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
        execution_id = self._build_execution_id(pipeline_result.execution_record.execution_id)
        previous_execution = scenario.executions.first()
        failure_summary = pipeline_result.execution_record.error_summary or ""
        diff_summary = self._build_execution_diff_summary(
            execution_status=execution_status,
            passed_count=pipeline_result.execution_record.passed_count,
            failed_count=failed_count,
            skipped_count=pipeline_result.execution_record.skipped_count,
            failure_summary=failure_summary,
            previous_execution=previous_execution,
        )
        execution = ScenarioExecutionRecord.objects.create(
            scenario=scenario,
            execution_id=execution_id,
            execution_status=execution_status,
            passed_count=pipeline_result.execution_record.passed_count,
            failed_count=failed_count,
            skipped_count=pipeline_result.execution_record.skipped_count,
            report_path=pipeline_result.execution_record.report_path or "",
            failure_summary=failure_summary,
            trigger_source="manual",
            based_on_revision_id=self._get_latest_revision_id(scenario),
            based_on_suggestion_id=self._get_latest_applied_suggestion_id(scenario),
            change_summary={},
            diff_summary=diff_summary,
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
        execution_history = self._build_execution_history(scenario)
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
            "execution_history": execution_history,
            "latest_diff_summary": self._build_latest_diff_summary(scenario),
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
            "source_summary": self._build_source_summary(scenario),
            "issue_codes": self._build_issue_codes(scenario),
            "latest_diff_summary": self._build_latest_diff_summary(scenario),
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

    @staticmethod
    def _build_execution_id(base_execution_id: str) -> str:
        """为重复执行场景生成唯一的执行记录标识。"""
        return f"{base_execution_id}_{uuid4().hex[:8]}"

    @staticmethod
    def _get_latest_revision_id(scenario: ScenarioRecord) -> str | None:
        """获取当前场景最近一次修订标识。"""
        latest_revision = scenario.revisions.order_by("-revised_at", "-id").first()
        return latest_revision.revision_id if latest_revision else None

    @staticmethod
    def _get_latest_applied_suggestion_id(scenario: ScenarioRecord) -> str | None:
        """获取当前场景最近一次已采纳建议标识。"""
        latest_suggestion = scenario.suggestions.filter(apply_status="applied").order_by("-updated_at", "-id").first()
        return latest_suggestion.suggestion_id if latest_suggestion else None

    def _apply_revision_patch(
        self,
        scenario: ScenarioRecord,
        reviser: str,
        revision_comment: str,
        scenario_patch: dict,
        suggestion_id: str | None,
    ) -> ScenarioRecord:
        """应用修订补丁并写入标准修订/审核留痕。"""
        applied_changes = self._apply_scenario_patch(scenario=scenario, scenario_patch=scenario_patch)
        scenario.review_status = "revised"
        scenario.current_stage = self._derive_stage(
            review_status=scenario.review_status,
            execution_status=scenario.execution_status,
        )
        scenario.save(update_fields=["review_status", "current_stage", "updated_at"])
        revision_metadata = {}
        if suggestion_id:
            revision_metadata["suggestion_id"] = suggestion_id
        revision_record = ScenarioRevisionRecord.objects.create(
            scenario=scenario,
            revision_id=f"revision-{uuid4().hex[:12]}",
            reviser=reviser,
            revision_comment=revision_comment,
            applied_changes=applied_changes,
            revised_at=datetime.now(UTC),
            metadata=revision_metadata,
        )
        ScenarioReviewRecord.objects.create(
            scenario=scenario,
            review_id=f"review-{uuid4().hex[:12]}",
            reviewer=reviser,
            review_comment=revision_comment,
            review_status="revised",
            reviewed_at=datetime.now(UTC),
            metadata={
                "applied_changes": applied_changes,
                "suggestion_id": suggestion_id,
                "revision_id": revision_record.revision_id,
            },
        )
        return scenario

    def _apply_scenario_patch(self, scenario: ScenarioRecord, scenario_patch: dict) -> dict:
        """把结构化修订补丁应用到场景与步骤持久化对象。"""
        applied_changes: dict[str, object] = {"scenario_fields": {}, "steps": []}
        scenario_fields = {
            "scenario_name",
            "scenario_desc",
            "priority",
            "module_id",
        }
        changed_scenario_fields: list[str] = []
        for field_name in scenario_fields:
            if field_name not in scenario_patch:
                continue
            setattr(scenario, field_name, scenario_patch[field_name])
            changed_scenario_fields.append(field_name)
            applied_changes["scenario_fields"][field_name] = scenario_patch[field_name]

        if changed_scenario_fields:
            scenario.save(update_fields=[*changed_scenario_fields, "updated_at"])

        step_patches = scenario_patch.get("steps") or []
        if step_patches:
            applied_changes["steps"] = self._apply_step_patches(scenario=scenario, step_patches=step_patches)
        return applied_changes

    @staticmethod
    def _apply_step_patches(scenario: ScenarioRecord, step_patches: list[dict]) -> list[dict]:
        """把结构化修订补丁应用到步骤及其原始载荷。"""
        applied_step_changes: list[dict] = []
        for step_patch in step_patches:
            step_id = step_patch.get("step_id")
            if not step_id:
                raise ScenarioServiceError(
                    code="scenario_step_patch_missing_step_id",
                    message="步骤修订补丁缺少 step_id。",
                    status_code=400,
                )
            try:
                step = scenario.steps.get(step_id=step_id)
            except ScenarioStepRecord.DoesNotExist as error:
                raise ScenarioServiceError(
                    code="scenario_step_not_found",
                    message=f"未找到待修订步骤: {step_id}",
                    status_code=404,
                ) from error

            raw_step = {}
            if isinstance(step.metadata, dict):
                raw_step = dict(step.metadata.get("raw_step") or {})
            changed_fields: dict[str, object] = {"step_id": step_id}
            update_fields: list[str] = []

            if "step_name" in step_patch:
                step.step_name = step_patch["step_name"]
                raw_step["step_name"] = step_patch["step_name"]
                update_fields.append("step_name")
                changed_fields["step_name"] = step_patch["step_name"]
            if "operation_id" in step_patch:
                step.operation_id = step_patch["operation_id"]
                raw_step["operation_id"] = step_patch["operation_id"]
                update_fields.append("operation_id")
                changed_fields["operation_id"] = step_patch["operation_id"]
            if "optional" in step_patch:
                step.optional = bool(step_patch["optional"])
                raw_step["optional"] = step.optional
                update_fields.append("optional")
                changed_fields["optional"] = step.optional
            if "retry_policy" in step_patch:
                step.retry_policy = step_patch["retry_policy"] or {}
                raw_step["retry_policy"] = step.retry_policy
                update_fields.append("retry_policy")
                changed_fields["retry_policy"] = step.retry_policy
            if "request" in step_patch:
                raw_step["request"] = step_patch["request"] or {}
                changed_fields["request"] = raw_step["request"]
            if "expected" in step_patch:
                raw_step["expected"] = step_patch["expected"] or {}
                changed_fields["expected"] = raw_step["expected"]
            if "uses" in step_patch:
                raw_step["uses"] = step_patch["uses"] or {}
                changed_fields["uses"] = raw_step["uses"]

            step.input_bindings = list((raw_step.get("uses") or {}).keys())
            step.expected_bindings = list((raw_step.get("expected") or {}).keys())
            step.metadata = {**(step.metadata or {}), "raw_step": raw_step}
            update_fields.extend(["input_bindings", "expected_bindings", "metadata"])
            step.save(update_fields=list(dict.fromkeys(update_fields)))
            applied_step_changes.append(changed_fields)
        return applied_step_changes
