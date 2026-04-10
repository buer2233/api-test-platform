"""V2 场景服务请求序列化定义。"""

from __future__ import annotations

from rest_framework import serializers


class FunctionalCaseImportRequestSerializer(serializers.Serializer):
    """功能测试用例导入请求校验器。"""

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

    capture_name = serializers.CharField()
    capture_payload = serializers.JSONField()


class ScenarioListQuerySerializer(serializers.Serializer):
    """场景列表筛选查询参数校验器。"""

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
