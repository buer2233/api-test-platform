"""V2 场景服务请求序列化定义。"""

from __future__ import annotations

from rest_framework import serializers


class FunctionalCaseImportRequestSerializer(serializers.Serializer):
    """功能测试用例导入请求校验器。"""

    project_code = serializers.CharField(required=False, allow_blank=True)
    environment_code = serializers.CharField(required=False, allow_blank=True)
    scenario_set_code = serializers.CharField(required=False, allow_blank=True)
    module_id = serializers.CharField(required=False, allow_blank=True)
    case_id = serializers.CharField()
    case_code = serializers.CharField(required=False, allow_blank=True)
    case_name = serializers.CharField()
    steps = serializers.ListField(child=serializers.DictField())
    priority = serializers.CharField(required=False, allow_blank=True)
    preconditions = serializers.ListField(child=serializers.CharField(), required=False)
    postconditions = serializers.ListField(child=serializers.CharField(), required=False)
    cleanup_required = serializers.BooleanField(required=False)


class TrafficCaptureImportRequestSerializer(serializers.Serializer):
    """抓包导入请求校验器。"""

    project_code = serializers.CharField(required=False, allow_blank=True)
    environment_code = serializers.CharField(required=False, allow_blank=True)
    scenario_set_code = serializers.CharField(required=False, allow_blank=True)
    capture_name = serializers.CharField()
    capture_payload = serializers.JSONField()


class TrafficCaptureConfirmRequestSerializer(serializers.Serializer):
    """抓包正式确认请求校验器。"""

    confirmer = serializers.CharField()
    confirm_comment = serializers.CharField(required=False, allow_blank=True)


class TrafficCaptureBindingConfirmRequestSerializer(serializers.Serializer):
    """抓包绑定确认请求校验器。"""

    confirmer = serializers.CharField()
    confirm_comment = serializers.CharField(required=False, allow_blank=True)
    step_bindings = serializers.ListField(child=serializers.DictField())


class ScenarioListQuerySerializer(serializers.Serializer):
    """场景列表筛选查询参数校验器。"""

    actor = serializers.CharField(required=False, allow_blank=True)
    project_code = serializers.CharField(required=False, allow_blank=True)
    environment_code = serializers.CharField(required=False, allow_blank=True)
    scenario_set_code = serializers.CharField(required=False, allow_blank=True)
    source_type = serializers.ChoiceField(
        choices=["functional_case", "traffic_capture", "ai_suggestion"],
        required=False,
    )
    review_status = serializers.ChoiceField(
        choices=["pending", "approved", "rejected", "revised"],
        required=False,
    )
    execution_status = serializers.ChoiceField(
        choices=["not_started", "running", "passed", "failed"],
        required=False,
    )
    issue_code = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        choices=["updated_desc", "updated_asc"],
        required=False,
        default="updated_desc",
    )


class BaselineVersionActivateSerializer(serializers.Serializer):
    """基线版本激活请求校验器。"""

    project_code = serializers.CharField()
    scenario_set_code = serializers.CharField()
    version_code = serializers.CharField()
    version_name = serializers.CharField(required=False, allow_blank=True)


class ProjectRoleAssignmentRequestSerializer(serializers.Serializer):
    """项目角色授权写入请求校验器。"""

    project_code = serializers.CharField()
    operator = serializers.CharField()
    subject_name = serializers.CharField()
    role_code = serializers.ChoiceField(
        choices=["viewer", "editor", "executor", "reviewer", "scheduler", "project_admin"]
    )


class ProjectRoleAssignmentQuerySerializer(serializers.Serializer):
    """项目角色授权查询参数校验器。"""

    project_code = serializers.CharField()
    subject_name = serializers.CharField(required=False, allow_blank=True)


class ScenarioAuditLogQuerySerializer(serializers.Serializer):
    """项目审计日志查询参数校验器。"""

    project_code = serializers.CharField(required=False, allow_blank=True)
    actor_name = serializers.CharField(required=False, allow_blank=True)
    action_type = serializers.CharField(required=False, allow_blank=True)
    action_result = serializers.ChoiceField(choices=["succeeded", "blocked"], required=False)


class ThemePreferenceRequestSerializer(serializers.Serializer):
    """主题切换写入请求校验器。"""

    theme_code = serializers.ChoiceField(choices=["dark", "light", "gray"])
    actor = serializers.CharField(required=False, allow_blank=True)


class CaptureSessionStartRequestSerializer(serializers.Serializer):
    """抓包会话启动请求校验器。"""

    project_code = serializers.CharField()
    module_code = serializers.CharField()
    submodule_code = serializers.CharField()
    operator = serializers.CharField()
    listen_port = serializers.IntegerField(min_value=1, max_value=65535)
    filter_rule = serializers.DictField(required=False)


class CaptureCandidateBuildRequestSerializer(serializers.Serializer):
    """抓包候选治理请求校验器。"""

    capture_records = serializers.ListField(child=serializers.DictField())


class GenerationConfirmRequestSerializer(serializers.Serializer):
    """生成确认请求校验器。"""

    project_code = serializers.CharField()
    model_code = serializers.CharField()
    case_code = serializers.CharField()
    selected_candidate_ids = serializers.ListField(child=serializers.CharField(), min_length=1)


class AiGovernancePolicyRequestSerializer(serializers.Serializer):
    """AI 治理策略写入请求校验器。"""

    project_code = serializers.CharField()
    operator = serializers.CharField()
    scope_type = serializers.ChoiceField(choices=["project", "module", "scenario_set"], required=False, default="project")
    scope_ref = serializers.CharField(required=False, allow_blank=True)
    suggestion_types = serializers.ListField(
        child=serializers.ChoiceField(choices=["assertion_completion", "low_confidence_repair", "step_patch"])
    )
    approval_mode = serializers.ChoiceField(choices=["manual_review"], required=False, default="manual_review")
    rollback_mode = serializers.ChoiceField(choices=["snapshot_restore"], required=False, default="snapshot_restore")
    auto_execution_enabled = serializers.BooleanField(required=False, default=False)


class AiGovernancePolicyQuerySerializer(serializers.Serializer):
    """AI 治理策略查询参数校验器。"""

    project_code = serializers.CharField()


class ScheduleScenarioItemSerializer(serializers.Serializer):
    """调度任务项请求校验器。"""

    scenario_id = serializers.CharField()
    retry_policy = serializers.JSONField(required=False)


class ScheduleBatchCreateRequestSerializer(serializers.Serializer):
    """调度批次创建请求校验器。"""

    project_code = serializers.CharField()
    environment_code = serializers.CharField()
    scheduler = serializers.CharField()
    dispatch_strategy = serializers.ChoiceField(choices=["immediate", "manual_queue"], required=False)
    workspace_root = serializers.CharField(required=False, allow_blank=True)
    scenario_items = ScheduleScenarioItemSerializer(many=True)


class ScheduleBatchListQuerySerializer(serializers.Serializer):
    """调度批次列表查询参数校验器。"""

    actor = serializers.CharField(required=False, allow_blank=True)
    project_code = serializers.CharField(required=False, allow_blank=True)


class ScheduleBatchDetailQuerySerializer(serializers.Serializer):
    """调度批次详情查询参数校验器。"""

    actor = serializers.CharField(required=False, allow_blank=True)


class ScheduleItemRetryRequestSerializer(serializers.Serializer):
    """调度任务项重试请求校验器。"""

    scheduler = serializers.CharField()
    workspace_root = serializers.CharField(required=False, allow_blank=True)


class ScheduleItemCancelRequestSerializer(serializers.Serializer):
    """调度任务项取消请求校验器。"""

    scheduler = serializers.CharField()
    cancel_reason = serializers.CharField(required=False, allow_blank=True)


class ScenarioExportRequestSerializer(serializers.Serializer):
    """场景导出请求校验器。"""

    project_code = serializers.CharField()
    export_root = serializers.CharField(required=False, allow_blank=True)


class ScenarioSuggestionRequestSerializer(serializers.Serializer):
    """建议创建请求校验器。"""

    requester = serializers.CharField()
    suggestion_type = serializers.ChoiceField(
        choices=["assertion_completion", "low_confidence_repair", "step_patch"],
    )


class ScenarioSuggestionQuerySerializer(serializers.Serializer):
    """建议查询请求校验器。"""

    actor = serializers.CharField(required=False, allow_blank=True)


class ScenarioSuggestionDecisionRequestSerializer(serializers.Serializer):
    """建议审批、拒绝与回退请求校验器。"""

    actor = serializers.CharField()
    decision_comment = serializers.CharField(required=False, allow_blank=True)
    rollback_comment = serializers.CharField(required=False, allow_blank=True)


class ScenarioSuggestionApplyRequestSerializer(serializers.Serializer):
    """建议采纳请求校验器。"""

    actor = serializers.CharField(required=False, allow_blank=True)
    reviser = serializers.CharField(required=False, allow_blank=True)
    revision_comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """统一兼容旧字段 `reviser` 和新字段 `actor`。"""
        actor_name = attrs.get("actor") or attrs.get("reviser")
        if not actor_name:
            raise serializers.ValidationError("actor 或 reviser 至少需要提供一个。")
        attrs["actor"] = actor_name
        return attrs


class ScenarioReviewRequestSerializer(serializers.Serializer):
    """场景审核请求校验器。"""

    review_status = serializers.ChoiceField(choices=["approved", "rejected"])
    reviewer = serializers.CharField()
    review_comment = serializers.CharField(required=False, allow_blank=True)


class ScenarioRevisionRequestSerializer(serializers.Serializer):
    """场景结构化修订请求校验器。"""

    reviser = serializers.CharField()
    revision_comment = serializers.CharField(required=False, allow_blank=True)
    scenario_name = serializers.CharField(required=False, allow_blank=True)
    scenario_desc = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(choices=["high", "medium", "low"], required=False)
    module_id = serializers.CharField(required=False, allow_blank=True)
    steps = serializers.ListField(child=serializers.DictField(), required=False)
