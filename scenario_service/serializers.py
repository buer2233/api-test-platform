"""V2 场景服务请求序列化定义。"""

from __future__ import annotations

from rest_framework import serializers


class FunctionalCaseImportRequestSerializer(serializers.Serializer):
    """功能测试用例导入请求校验器。"""

    project_code = serializers.CharField(required=False, allow_blank=True)
    environment_code = serializers.CharField(required=False, allow_blank=True)
    scenario_set_code = serializers.CharField(required=False, allow_blank=True)
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


class ScenarioSuggestionApplyRequestSerializer(serializers.Serializer):
    """建议采纳请求校验器。"""

    reviser = serializers.CharField()
    revision_comment = serializers.CharField(required=False, allow_blank=True)


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
