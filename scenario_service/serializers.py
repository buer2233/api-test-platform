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
