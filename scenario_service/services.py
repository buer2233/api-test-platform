"""V2 场景服务应用层。"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import uuid4

from django.db import transaction

from platform_core.functional_cases import FunctionalCaseDraftParser
from platform_core.models import FunctionalCaseDraft
from platform_core.scenario_execution import ScenarioExecutionBindingError, ScenarioExecutionPipeline
from platform_core.services import PlatformApplicationService
from platform_core.traffic_capture import TrafficCaptureDraftParser
from scenario_service.governance import GovernanceBootstrapService
from scenario_service.models import (
    ProjectRoleAssignmentRecord,
    ScenarioExecutionRecord,
    ScenarioAuditLogRecord,
    ScenarioRecord,
    ScenarioRevisionRecord,
    ScenarioReviewRecord,
    ScenarioSourceRecord,
    ScenarioSuggestionRecord,
    ScenarioStepRecord,
    TrafficCaptureFormalizationRecord,
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


SUPER_ADMIN_ACTOR = "platform-admin"
BUILTIN_ACTOR_PERMISSIONS = {
    SUPER_ADMIN_ACTOR: {
        "can_view": True,
        "can_edit": True,
        "can_execute": True,
        "can_review": True,
        "can_schedule": True,
        "can_grant": True,
    },
    "qa-owner": {
        "can_view": True,
        "can_edit": True,
        "can_execute": True,
        "can_review": True,
        "can_schedule": True,
        "can_grant": True,
    },
    "qa-reviewer": {
        "can_view": True,
        "can_edit": False,
        "can_execute": False,
        "can_review": True,
        "can_schedule": False,
        "can_grant": False,
    },
}
ROLE_PERMISSION_TEMPLATES = {
    "viewer": {
        "can_view": True,
        "can_edit": False,
        "can_execute": False,
        "can_review": False,
        "can_schedule": False,
        "can_grant": False,
    },
    "editor": {
        "can_view": True,
        "can_edit": True,
        "can_execute": False,
        "can_review": False,
        "can_schedule": False,
        "can_grant": False,
    },
    "executor": {
        "can_view": True,
        "can_edit": False,
        "can_execute": True,
        "can_review": False,
        "can_schedule": False,
        "can_grant": False,
    },
    "reviewer": {
        "can_view": True,
        "can_edit": False,
        "can_execute": False,
        "can_review": True,
        "can_schedule": False,
        "can_grant": False,
    },
    "scheduler": {
        "can_view": True,
        "can_edit": False,
        "can_execute": True,
        "can_review": False,
        "can_schedule": True,
        "can_grant": False,
    },
    "project_admin": {
        "can_view": True,
        "can_edit": True,
        "can_execute": True,
        "can_review": True,
        "can_schedule": True,
        "can_grant": True,
    },
}


class FunctionalCaseScenarioService:
    """把多来源场景草稿接入 Django 持久化层。"""

    def __init__(
        self,
        parser: FunctionalCaseDraftParser | None = None,
        traffic_capture_parser: TrafficCaptureDraftParser | None = None,
        application_service: PlatformApplicationService | None = None,
        scenario_execution_pipeline: ScenarioExecutionPipeline | None = None,
        suggestion_provider: BaseSuggestionProvider | None = None,
        governance_service: GovernanceBootstrapService | None = None,
    ) -> None:
        """装配解析器与状态校验能力。"""
        self.parser = parser or FunctionalCaseDraftParser()
        self.traffic_capture_parser = traffic_capture_parser or TrafficCaptureDraftParser()
        self.application_service = application_service or PlatformApplicationService()
        self.scenario_execution_pipeline = scenario_execution_pipeline or ScenarioExecutionPipeline()
        self.suggestion_provider = suggestion_provider or RuleBasedSuggestionProvider()
        self.governance_service = governance_service or GovernanceBootstrapService()

    @transaction.atomic
    def import_functional_case(self, payload: dict) -> ScenarioRecord:
        """导入功能测试用例并持久化为场景草稿。"""
        draft = self.parser.parse_payload(
            raw_case=payload,
            source_name=payload.get("case_code") or payload.get("case_id") or "api_request",
        )
        governance_context = self.governance_service.resolve_context(
            project_code=payload.get("project_code"),
            environment_code=payload.get("environment_code"),
            scenario_set_code=payload.get("scenario_set_code"),
        )
        return self._persist_scenario_draft(draft=draft, governance_context=governance_context)

    @transaction.atomic
    def import_traffic_capture(
        self,
        capture_name: str,
        capture_payload: dict,
        project_code: str | None = None,
        environment_code: str | None = None,
        scenario_set_code: str | None = None,
    ) -> ScenarioRecord:
        """导入抓包数据并持久化为场景草稿。"""
        draft = self.traffic_capture_parser.parse_payload(
            raw_capture=capture_payload,
            source_name=capture_name or "traffic_capture",
        )
        governance_context = self.governance_service.resolve_context(
            project_code=project_code,
            environment_code=environment_code,
            scenario_set_code=scenario_set_code,
        )
        scenario = self._persist_scenario_draft(draft=draft, governance_context=governance_context)
        self._create_traffic_capture_formalization(scenario=scenario)
        return scenario

    def _persist_scenario_draft(self, draft: FunctionalCaseDraft, governance_context) -> ScenarioRecord:
        """把统一场景草稿对象持久化为场景与步骤记录。"""
        scoped_scenario_id = self.governance_service.build_project_scoped_scenario_id(
            project_code=governance_context.project.project_code,
            scenario_id=draft.scenario.scenario_id,
        )
        if ScenarioRecord.objects.filter(
            project=governance_context.project,
            scenario_code=draft.scenario.scenario_code,
        ).exists():
            raise ScenarioServiceError(
                code="scenario_already_exists",
                message="场景已存在，请修改场景标识后再导入。",
                status_code=400,
            )
        scenario = ScenarioRecord.objects.create(
            scenario_id=scoped_scenario_id,
            scenario_code=draft.scenario.scenario_code,
            scenario_name=draft.scenario.scenario_name,
            project=governance_context.project,
            environment=governance_context.environment,
            scenario_set=governance_context.scenario_set,
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
                    step_id=self.governance_service.build_project_scoped_step_id(
                        project_code=governance_context.project.project_code,
                        step_id=step.step_id,
                    ),
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
    def _build_role_assignment_summary(assignment: ProjectRoleAssignmentRecord) -> dict:
        """构造项目角色授权摘要。"""
        return {
            "assignment_id": assignment.assignment_id,
            "project_id": assignment.project.project_id,
            "project_code": assignment.project.project_code,
            "subject_name": assignment.subject_name,
            "role_code": assignment.role_code,
            "permissions": {
                "can_view": assignment.can_view,
                "can_edit": assignment.can_edit,
                "can_execute": assignment.can_execute,
                "can_review": assignment.can_review,
                "can_schedule": assignment.can_schedule,
                "can_grant": assignment.can_grant,
            },
            "granted_by": assignment.granted_by,
            "is_active": assignment.is_active,
            "created_at": assignment.created_at.isoformat(),
            "updated_at": assignment.updated_at.isoformat(),
        }

    @staticmethod
    def _build_audit_log_summary(audit_log: ScenarioAuditLogRecord) -> dict:
        """构造审计日志摘要。"""
        return {
            "audit_id": audit_log.audit_id,
            "project_code": audit_log.project.project_code if audit_log.project else "",
            "scenario_id": audit_log.scenario.scenario_id if audit_log.scenario else "",
            "execution_id": audit_log.execution.execution_id if audit_log.execution else "",
            "actor_name": audit_log.actor_name,
            "action_type": audit_log.action_type,
            "action_result": audit_log.action_result,
            "target_type": audit_log.target_type,
            "target_id": audit_log.target_id,
            "detail_message": audit_log.detail_message,
            "metadata": audit_log.metadata,
            "created_at": audit_log.created_at.isoformat(),
        }

    @staticmethod
    def _build_traffic_capture_formalization_summary(formalization: TrafficCaptureFormalizationRecord) -> dict:
        """构造抓包正式执行治理摘要。"""
        return {
            "confirmation_id": formalization.confirmation_id,
            "project_code": formalization.project.project_code,
            "environment_code": formalization.environment.environment_code,
            "confirmation_status": formalization.confirmation_status,
            "binding_status": formalization.binding_status,
            "execution_readiness": formalization.execution_readiness,
            "confirmed_by": formalization.confirmed_by,
            "bindings_confirmed_by": formalization.bindings_confirmed_by,
            "last_execution_id": formalization.last_execution_id,
            "metadata": formalization.metadata,
            "created_at": formalization.created_at.isoformat(),
            "updated_at": formalization.updated_at.isoformat(),
        }

    @staticmethod
    def _is_traffic_capture_scenario(scenario: ScenarioRecord) -> bool:
        """判断当前场景是否来自抓包导入路线。"""
        return (scenario.metadata or {}).get("source_type") == "traffic_capture"

    @staticmethod
    def _get_traffic_capture_formalization(
        scenario: ScenarioRecord,
    ) -> TrafficCaptureFormalizationRecord | None:
        """读取抓包场景的正式执行治理对象。"""
        if not FunctionalCaseScenarioService._is_traffic_capture_scenario(scenario):
            return None
        try:
            return scenario.traffic_capture_formalization
        except TrafficCaptureFormalizationRecord.DoesNotExist:
            return None

    def _create_traffic_capture_formalization(
        self,
        *,
        scenario: ScenarioRecord,
    ) -> TrafficCaptureFormalizationRecord | None:
        """为抓包场景初始化正式执行治理对象。"""
        if not self._is_traffic_capture_scenario(scenario):
            return None
        if scenario.project is None or scenario.environment is None:
            raise ScenarioServiceError(
                code="traffic_capture_governance_context_missing",
                message="抓包场景缺少项目或环境上下文，无法初始化正式执行治理对象。",
                status_code=400,
            )
        formalization, _ = TrafficCaptureFormalizationRecord.objects.get_or_create(
            scenario=scenario,
            defaults={
                "confirmation_id": f"capture-formalization-{scenario.scenario_id}",
                "project": scenario.project,
                "environment": scenario.environment,
                "confirmation_status": "draft",
                "binding_status": "pending",
                "execution_readiness": "blocked",
                "metadata": {
                    "source_type": "traffic_capture",
                    "scenario_code": scenario.scenario_code,
                },
            },
        )
        return formalization

    def _validate_traffic_capture_step_bindings(self, step_bindings: list[dict]) -> None:
        """校验抓包步骤绑定确认请求中的公开基线操作映射。"""
        if not step_bindings:
            raise ScenarioServiceError(
                code="traffic_capture_step_bindings_required",
                message="抓包正式绑定确认至少需要一条步骤绑定。",
                status_code=400,
            )
        supported_operations = self.scenario_execution_pipeline.SUPPORTED_OPERATIONS
        for binding in step_bindings:
            operation_id = binding.get("operation_id")
            if not operation_id or operation_id not in supported_operations:
                raise ScenarioServiceError(
                    code="unsupported_public_baseline_operation",
                    message=f"未绑定可执行的公开基线操作: {operation_id}",
                    status_code=400,
                )

    @staticmethod
    def _clear_capture_review_issues(scenario: ScenarioRecord) -> None:
        """在绑定确认完成后清理抓包候选态问题标记。"""
        scenario.issues = [
            issue
            for issue in scenario.issues
            if issue.get("issue_code") != "capture_operation_needs_review"
        ]
        scenario.issue_count = len(scenario.issues)
        scenario.save(update_fields=["issues", "issue_count", "updated_at"])
        scenario.sources.filter(entity_type="step").update(confidence="high", issue_tags=[])

    def confirm_traffic_capture(
        self,
        *,
        scenario_id: str,
        confirmer: str,
        confirm_comment: str = "",
    ) -> dict:
        """确认抓包场景可进入正式绑定阶段。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        if not self._is_traffic_capture_scenario(scenario):
            raise ScenarioServiceError(
                code="traffic_capture_scenario_required",
                message="当前场景不是抓包导入场景，不能执行抓包正式确认。",
                status_code=400,
            )
        if scenario.review_status != "approved":
            raise ScenarioServiceError(
                code="traffic_capture_review_required",
                message="抓包场景需先审核通过，才能进入正式确认。",
                status_code=400,
            )
        self._authorize_project_action(
            project=scenario.project,
            actor_name=confirmer,
            action_type="confirm_traffic_capture",
            required_permission="can_review",
            target_type="scenario",
            target_id=scenario.scenario_id,
            scenario=scenario,
            detail_message="尝试确认抓包场景进入正式绑定阶段。",
        )
        formalization = self._create_traffic_capture_formalization(scenario=scenario)
        assert formalization is not None
        formalization.confirmation_status = "confirmed"
        formalization.execution_readiness = "ready" if formalization.binding_status == "confirmed" else "blocked"
        formalization.confirmed_by = confirmer
        formalization.metadata = {
            **(formalization.metadata or {}),
            "confirm_comment": confirm_comment,
            "confirmed_at": datetime.now(UTC).isoformat(),
        }
        formalization.save(
            update_fields=[
                "confirmation_status",
                "execution_readiness",
                "confirmed_by",
                "metadata",
                "updated_at",
            ]
        )
        self._create_audit_log(
            project=scenario.project,
            actor_name=confirmer,
            action_type="confirm_traffic_capture",
            action_result="succeeded",
            target_type="scenario",
            target_id=scenario.scenario_id,
            scenario=scenario,
            detail_message="已确认抓包场景进入正式绑定阶段。",
            metadata={"confirmation_status": formalization.confirmation_status},
        )
        return self._build_traffic_capture_formalization_summary(formalization)

    def confirm_traffic_capture_bindings(
        self,
        *,
        scenario_id: str,
        confirmer: str,
        step_bindings: list[dict],
        confirm_comment: str = "",
    ) -> dict:
        """确认抓包步骤的正式操作绑定与变量绑定。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        if not self._is_traffic_capture_scenario(scenario):
            raise ScenarioServiceError(
                code="traffic_capture_scenario_required",
                message="当前场景不是抓包导入场景，不能执行抓包绑定确认。",
                status_code=400,
            )
        self._authorize_project_action(
            project=scenario.project,
            actor_name=confirmer,
            action_type="confirm_traffic_capture_bindings",
            required_permission="can_review",
            target_type="scenario",
            target_id=scenario.scenario_id,
            scenario=scenario,
            detail_message="尝试确认抓包步骤绑定。",
        )
        formalization = self._create_traffic_capture_formalization(scenario=scenario)
        assert formalization is not None
        if formalization.confirmation_status != "confirmed":
            raise ScenarioServiceError(
                code="traffic_capture_confirmation_required",
                message="抓包场景需先完成正式确认，才能确认步骤绑定。",
                status_code=400,
            )
        self._validate_traffic_capture_step_bindings(step_bindings=step_bindings)
        with transaction.atomic():
            self._apply_step_patches(scenario=scenario, step_patches=step_bindings)
            self._clear_capture_review_issues(scenario)
            formalization.binding_status = "confirmed"
            formalization.execution_readiness = "ready"
            formalization.bindings_confirmed_by = confirmer
            formalization.metadata = {
                **(formalization.metadata or {}),
                "binding_confirm_comment": confirm_comment,
                "binding_confirmed_at": datetime.now(UTC).isoformat(),
                "binding_step_count": len(step_bindings),
            }
            formalization.save(
                update_fields=[
                    "binding_status",
                    "execution_readiness",
                    "bindings_confirmed_by",
                    "metadata",
                    "updated_at",
                ]
            )
            self._create_audit_log(
                project=scenario.project,
                actor_name=confirmer,
                action_type="confirm_traffic_capture_bindings",
                action_result="succeeded",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="已完成抓包步骤正式绑定确认。",
                metadata={"binding_status": formalization.binding_status, "step_count": len(step_bindings)},
            )
        return self._build_traffic_capture_formalization_summary(formalization)

    def _ensure_traffic_capture_execution_ready(
        self,
        *,
        scenario: ScenarioRecord,
        actor_name: str | None,
    ) -> TrafficCaptureFormalizationRecord | None:
        """在执行前校验抓包场景是否已完成正式确认与绑定确认。"""
        formalization = self._get_traffic_capture_formalization(scenario)
        if formalization is None:
            return None
        if formalization.confirmation_status == "confirmed" and formalization.binding_status == "confirmed":
            return formalization
        if actor_name:
            self._create_audit_log(
                project=scenario.project,
                actor_name=actor_name,
                action_type="execute_scenario",
                action_result="blocked",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="抓包场景尚未完成正式确认与绑定确认，禁止触发正式执行。",
                metadata={"reason_code": "traffic_capture_formalization_required"},
            )
        raise ScenarioServiceError(
            code="traffic_capture_formalization_required",
            message="抓包场景需先完成正式确认与绑定确认，才能触发正式执行。",
            status_code=400,
        )

    @staticmethod
    def _resolve_role_permissions(role_code: str) -> dict[str, bool]:
        """返回角色编码对应的权限模板。"""
        try:
            return ROLE_PERMISSION_TEMPLATES[role_code]
        except KeyError as error:
            raise ScenarioServiceError(
                code="project_role_code_invalid",
                message=f"未支持的项目角色编码: {role_code}",
                status_code=400,
            ) from error

    @staticmethod
    def _get_project_role_assignment(
        *,
        project,
        subject_name: str,
    ) -> ProjectRoleAssignmentRecord | None:
        """加载项目成员当前生效的角色授权记录。"""
        return (
            ProjectRoleAssignmentRecord.objects.filter(
                project=project,
                subject_name=subject_name,
                is_active=True,
            )
            .order_by("-updated_at", "-id")
            .first()
        )

    @staticmethod
    def _create_audit_log(
        *,
        project,
        actor_name: str,
        action_type: str,
        action_result: str,
        target_type: str,
        target_id: str,
        scenario: ScenarioRecord | None = None,
        execution: ScenarioExecutionRecord | None = None,
        detail_message: str = "",
        metadata: dict | None = None,
    ) -> ScenarioAuditLogRecord:
        """写入一条治理动作审计日志。"""
        return ScenarioAuditLogRecord.objects.create(
            audit_id=f"audit-{uuid4().hex[:12]}",
            project=project,
            scenario=scenario,
            execution=execution,
            actor_name=actor_name,
            action_type=action_type,
            action_result=action_result,
            target_type=target_type,
            target_id=target_id,
            detail_message=detail_message,
            metadata=metadata or {},
        )

    def _authorize_project_action(
        self,
        *,
        project,
        actor_name: str,
        action_type: str,
        required_permission: str,
        target_type: str,
        target_id: str,
        scenario: ScenarioRecord | None = None,
        detail_message: str = "",
    ) -> ProjectRoleAssignmentRecord | None:
        """校验 actor 是否具备项目级动作权限，不通过时写入阻断日志。"""
        builtin_permissions = BUILTIN_ACTOR_PERMISSIONS.get(actor_name)
        if builtin_permissions and builtin_permissions.get(required_permission):
            return None
        assignment = self._get_project_role_assignment(project=project, subject_name=actor_name)
        if assignment is None or not getattr(assignment, required_permission):
            self._create_audit_log(
                project=project,
                actor_name=actor_name,
                action_type=action_type,
                action_result="blocked",
                target_type=target_type,
                target_id=target_id,
                scenario=scenario,
                detail_message=detail_message or "当前成员缺少项目动作权限。",
                metadata={"required_permission": required_permission},
            )
            raise ScenarioServiceError(
                code="project_action_forbidden",
                message="当前成员无权执行该项目动作。",
                status_code=403,
            )
        return assignment

    def assign_project_role(
        self,
        *,
        project_code: str,
        operator: str,
        subject_name: str,
        role_code: str,
    ) -> dict:
        """为项目成员写入或更新角色授权记录。"""
        context = self.governance_service.resolve_context(project_code=project_code)
        if operator != SUPER_ADMIN_ACTOR:
            self._authorize_project_action(
                project=context.project,
                actor_name=operator,
                action_type="assign_project_role",
                required_permission="can_grant",
                target_type="project",
                target_id=context.project.project_id,
                detail_message="尝试为项目成员分配角色。",
            )
        permissions = self._resolve_role_permissions(role_code=role_code)
        with transaction.atomic():
            assignment, created = ProjectRoleAssignmentRecord.objects.update_or_create(
                project=context.project,
                subject_name=subject_name,
                defaults={
                    "assignment_id": f"assignment-{context.project.project_code}-{subject_name}",
                    "role_code": role_code,
                    "can_view": permissions["can_view"],
                    "can_edit": permissions["can_edit"],
                    "can_execute": permissions["can_execute"],
                    "can_review": permissions["can_review"],
                    "can_schedule": permissions["can_schedule"],
                    "can_grant": permissions["can_grant"],
                    "granted_by": operator,
                    "is_active": True,
                    "metadata": {},
                },
            )
            self._create_audit_log(
                project=context.project,
                actor_name=operator,
                action_type="assign_project_role",
                action_result="succeeded",
                target_type="project_role_assignment",
                target_id=assignment.assignment_id,
                detail_message=f"已为 {subject_name} 分配角色 {role_code}。",
                metadata={
                    "subject_name": subject_name,
                    "role_code": role_code,
                    "created": created,
                },
            )
        return self._build_role_assignment_summary(assignment)

    def list_project_roles(
        self,
        *,
        project_code: str,
        subject_name: str | None = None,
    ) -> list[dict]:
        """查询项目成员角色授权记录。"""
        queryset = ProjectRoleAssignmentRecord.objects.filter(project__project_code=project_code, is_active=True)
        if subject_name:
            queryset = queryset.filter(subject_name=subject_name)
        return [self._build_role_assignment_summary(item) for item in queryset.order_by("subject_name", "id")]

    def list_audit_logs(
        self,
        *,
        project_code: str | None = None,
        actor_name: str | None = None,
        action_type: str | None = None,
        action_result: str | None = None,
    ) -> list[dict]:
        """按治理维度筛选审计日志记录。"""
        queryset = ScenarioAuditLogRecord.objects.all()
        if project_code:
            queryset = queryset.filter(project__project_code=project_code)
        if actor_name:
            queryset = queryset.filter(actor_name=actor_name)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        if action_result:
            queryset = queryset.filter(action_result=action_result)
        return [self._build_audit_log_summary(item) for item in queryset.order_by("-created_at", "-id")]

    def _build_governance_summary(self, scenario: ScenarioRecord) -> dict:
        """构造场景级治理上下文摘要。"""
        self.governance_service.ensure_bootstrap()
        project = scenario.project
        environment = scenario.environment
        scenario_set = scenario.scenario_set
        if project is None or environment is None or scenario_set is None:
            default_context = self.governance_service.ensure_bootstrap()
            project = project or default_context.project
            environment = environment or default_context.environment
            scenario_set = scenario_set or default_context.scenario_set
        baseline_version = self.governance_service.get_active_baseline_version(scenario_set=scenario_set)
        return {
            "project": self.governance_service.build_project_summary(project),
            "environment": self.governance_service.build_environment_summary(environment),
            "scenario_set": self.governance_service.build_scenario_set_summary(scenario_set),
            "baseline_version": self.governance_service.build_baseline_version_summary(baseline_version)
            if baseline_version
            else None,
        }

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

    def get_scenario_detail(self, scenario_id: str, actor: str | None = None) -> dict:
        """返回场景详情结构。"""
        self.governance_service.ensure_bootstrap()
        scenario = self._get_scenario(scenario_id=scenario_id)
        if actor:
            self._authorize_project_action(
                project=scenario.project,
                actor_name=actor,
                action_type="view_scenario",
                required_permission="can_view",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="尝试查看场景详情。",
            )
            self._create_audit_log(
                project=scenario.project,
                actor_name=actor,
                action_type="view_scenario",
                action_result="succeeded",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="已查看场景详情。",
            )
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
            **self._build_governance_summary(scenario),
        }

    def list_scenarios(self, filters: dict | None = None) -> list[dict]:
        """按筛选条件返回供入口页消费的场景摘要列表。"""
        self.governance_service.ensure_bootstrap()
        filters = filters or {}
        queryset = ScenarioRecord.objects.all()
        actor = filters.get("actor")

        project_code = filters.get("project_code")
        if project_code:
            queryset = queryset.filter(project__project_code=project_code)
            if actor:
                project = self.governance_service.resolve_context(project_code=project_code).project
                self._authorize_project_action(
                    project=project,
                    actor_name=actor,
                    action_type="list_scenarios",
                    required_permission="can_view",
                    target_type="project",
                    target_id=project.project_id,
                    detail_message="尝试按项目筛选场景列表。",
                )
        elif actor and not BUILTIN_ACTOR_PERMISSIONS.get(actor, {}).get("can_view"):
            assignments = ProjectRoleAssignmentRecord.objects.filter(subject_name=actor, is_active=True, can_view=True)
            queryset = queryset.filter(project__in=[item.project for item in assignments])

        environment_code = filters.get("environment_code")
        if environment_code:
            queryset = queryset.filter(environment__environment_code=environment_code)

        scenario_set_code = filters.get("scenario_set_code")
        if scenario_set_code:
            queryset = queryset.filter(scenario_set__scenario_set_code=scenario_set_code)

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

    def get_governance_context(self) -> dict:
        """返回治理入口使用的上下文树。"""
        return self.governance_service.build_context_tree()

    def activate_baseline_version(
        self,
        *,
        project_code: str,
        scenario_set_code: str,
        version_code: str,
        version_name: str | None = None,
    ) -> dict:
        """切换场景集当前生效版本并返回更新后的治理摘要。"""
        context = self.governance_service.activate_baseline_version(
            project_code=project_code,
            scenario_set_code=scenario_set_code,
            version_code=version_code,
            version_name=version_name,
        )
        return self.governance_service.build_context_summary(context)

    def export_scenario_bundle(
        self,
        scenario_id: str,
        *,
        project_code: str,
        export_root: str | Path | None = None,
    ) -> dict:
        """按项目归属导出场景详情快照。"""
        self.governance_service.ensure_bootstrap()
        scenario = self._get_scenario(scenario_id=scenario_id)
        try:
            governance_context = self.governance_service.resolve_export_context(
                scenario=scenario,
                project_code=project_code,
            )
        except ValueError as error:
            if str(error) == "project_context_mismatch":
                raise ScenarioServiceError(
                    code="project_context_mismatch",
                    message="导出请求中的项目上下文与场景归属不一致。",
                    status_code=400,
                ) from error
            raise
        target_root = Path(export_root) if export_root else None
        export_path = self.governance_service.build_export_path(
            context=governance_context,
            scenario=scenario,
            export_root=target_root,
        )
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_payload = self.get_scenario_detail(scenario_id=scenario_id)
        export_path.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "scenario_id": scenario.scenario_id,
            "project": self.governance_service.build_project_summary(governance_context.project),
            "environment": self.governance_service.build_environment_summary(governance_context.environment),
            "scenario_set": self.governance_service.build_scenario_set_summary(governance_context.scenario_set),
            "baseline_version": self.governance_service.build_baseline_version_summary(governance_context.baseline_version),
            "export_path": str(export_path),
        }

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

    def review_scenario(
        self,
        scenario_id: str,
        review_status: str,
        reviewer: str,
        review_comment: str | None = None,
        ) -> ScenarioRecord:
        """执行场景审核并写入留痕记录。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        self._authorize_project_action(
            project=scenario.project,
            actor_name=reviewer,
            action_type="review_scenario",
            required_permission="can_review",
            target_type="scenario",
            target_id=scenario.scenario_id,
            scenario=scenario,
            detail_message="尝试审核场景。",
        )
        with transaction.atomic():
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
            self._create_audit_log(
                project=scenario.project,
                actor_name=reviewer,
                action_type="review_scenario",
                action_result="succeeded",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message=f"已将场景审核状态更新为 {review_status}。",
                metadata={"review_status": review_status},
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

    def request_execution(
        self,
        scenario_id: str,
        project_code: str | None = None,
        environment_code: str | None = None,
        workspace_root: str | Path | None = None,
        operator: str | None = None,
    ) -> ScenarioExecutionRecord:
        """执行场景并回写统一结果摘要。"""
        self.governance_service.ensure_bootstrap()
        scenario = self._get_scenario(scenario_id=scenario_id)
        if scenario.review_status != "approved":
            raise ScenarioServiceError(
                code="scenario_not_approved",
                message="场景未确认，禁止触发正式执行。",
                status_code=400,
            )
        if not project_code or not environment_code:
            raise ScenarioServiceError(
                code="governance_context_required",
                message="执行必须显式指定项目和环境。",
                status_code=400,
            )
        if operator:
            self._authorize_project_action(
                project=scenario.project,
                actor_name=operator,
                action_type="execute_scenario",
                required_permission="can_execute",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="尝试触发场景执行。",
            )
        formalization = self._ensure_traffic_capture_execution_ready(scenario=scenario, actor_name=operator)
        try:
            governance_context = self.governance_service.resolve_execution_context(
                scenario=scenario,
                project_code=project_code,
                environment_code=environment_code,
            )
        except ValueError as error:
            if str(error) == "project_context_mismatch":
                raise ScenarioServiceError(
                    code="project_context_mismatch",
                    message="执行请求中的项目上下文与场景归属不一致。",
                    status_code=400,
                ) from error
            if str(error) == "environment_context_mismatch":
                raise ScenarioServiceError(
                    code="environment_context_mismatch",
                    message="执行请求中的环境上下文与场景绑定不一致。",
                    status_code=400,
                ) from error
            raise
        baseline_version = governance_context.baseline_version
        resolved_workspace_root = (
            Path(workspace_root)
            if workspace_root
            else self._build_default_workspace_root(scenario=scenario, governance_context=governance_context)
        )
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
        with transaction.atomic():
            execution = ScenarioExecutionRecord.objects.create(
                scenario=scenario,
                project=scenario.project,
                environment=scenario.environment,
                scenario_set=scenario.scenario_set,
                baseline_version=baseline_version,
                execution_id=execution_id,
                execution_status=execution_status,
                passed_count=pipeline_result.execution_record.passed_count,
                failed_count=failed_count,
                skipped_count=pipeline_result.execution_record.skipped_count,
                workspace_root=pipeline_result.asset_manifest.workspace_root,
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
            if formalization is not None:
                formalization.last_execution_id = execution.execution_id
                formalization.metadata = {
                    **(formalization.metadata or {}),
                    "last_execution_at": datetime.now(UTC).isoformat(),
                }
                formalization.save(update_fields=["last_execution_id", "metadata", "updated_at"])
            if operator:
                self._create_audit_log(
                    project=scenario.project,
                    actor_name=operator,
                    action_type="execute_scenario",
                    action_result="succeeded",
                    target_type="scenario",
                    target_id=scenario.scenario_id,
                    scenario=scenario,
                    execution=execution,
                    detail_message="已触发场景执行并写回结果。",
                    metadata={"execution_id": execution.execution_id},
                )
        return execution

    def get_scenario_result(self, scenario_id: str, actor: str | None = None) -> dict:
        """返回统一结果查询摘要。"""
        scenario = self._get_scenario(scenario_id=scenario_id)
        if actor:
            self._authorize_project_action(
                project=scenario.project,
                actor_name=actor,
                action_type="view_scenario_result",
                required_permission="can_view",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="尝试查看场景结果。",
            )
            self._create_audit_log(
                project=scenario.project,
                actor_name=actor,
                action_type="view_scenario_result",
                action_result="succeeded",
                target_type="scenario",
                target_id=scenario.scenario_id,
                scenario=scenario,
                detail_message="已查看场景结果摘要。",
            )
        execution = scenario.executions.first()
        execution_status = execution.execution_status if execution else scenario.execution_status
        execution_history = self._build_execution_history(scenario)
        result = {
            "scenario_id": scenario.scenario_id,
            "scenario_code": scenario.scenario_code,
            "scenario_name": scenario.scenario_name,
            **self._build_governance_summary(scenario),
            "review_status": scenario.review_status,
            "execution_status": execution_status,
            "latest_execution_id": execution.execution_id if execution else scenario.latest_execution_id,
            "step_count": scenario.step_count,
            "issue_count": scenario.issue_count,
            "passed_count": execution.passed_count if execution else scenario.passed_count,
            "failed_count": execution.failed_count if execution else scenario.failed_count,
            "skipped_count": execution.skipped_count if execution else scenario.skipped_count,
            "workspace_root": execution.workspace_root if execution and execution.workspace_root else scenario.workspace_root,
            "report_path": execution.report_path if execution and execution.report_path else scenario.report_path,
            "failure_summary": execution.failure_summary if execution else "",
            "execution_history": execution_history,
            "latest_diff_summary": self._build_latest_diff_summary(scenario),
        }
        formalization = self._get_traffic_capture_formalization(scenario)
        if formalization is not None:
            result["traffic_capture_formalization"] = self._build_traffic_capture_formalization_summary(formalization)
        return result

    def build_scenario_summary(self, scenario: ScenarioRecord) -> dict:
        """构造统一场景摘要。"""
        governance_summary = self._build_governance_summary(scenario)
        summary = {
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
            **governance_summary,
        }
        formalization = self._get_traffic_capture_formalization(scenario)
        if formalization is not None:
            summary["traffic_capture_formalization"] = self._build_traffic_capture_formalization_summary(formalization)
        return summary

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

    def _build_default_workspace_root(self, *, scenario: ScenarioRecord, governance_context) -> Path:
        """为未显式指定路径的执行请求构造默认工作区目录。"""
        return self.governance_service.build_workspace_root(
            context=governance_context,
            scenario=scenario,
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
