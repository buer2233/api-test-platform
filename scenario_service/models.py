"""V2 场景服务持久化模型。"""

from __future__ import annotations

from django.db import models


class ScenarioRecord(models.Model):
    """场景草稿与正式场景的持久化记录。"""

    scenario_id = models.CharField(max_length=128, unique=True)
    scenario_code = models.CharField(max_length=128)
    scenario_name = models.CharField(max_length=255)
    module_id = models.CharField(max_length=128, null=True, blank=True)
    scenario_desc = models.TextField(null=True, blank=True)
    source_ids = models.JSONField(default=list)
    priority = models.CharField(max_length=32, default="medium")
    review_status = models.CharField(max_length=32, default="pending")
    execution_status = models.CharField(max_length=32, default="not_started")
    current_stage = models.CharField(max_length=32, default="draft")
    issue_count = models.PositiveIntegerField(default=0)
    step_count = models.PositiveIntegerField(default=0)
    workspace_root = models.CharField(max_length=255, null=True, blank=True)
    report_path = models.CharField(max_length=255, null=True, blank=True)
    latest_execution_id = models.CharField(max_length=128, null=True, blank=True)
    passed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    issues = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """返回便于后台查看的场景标识。"""
        return f"{self.scenario_code}({self.review_status})"


class ScenarioStepRecord(models.Model):
    """场景步骤持久化记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="steps", on_delete=models.CASCADE)
    step_id = models.CharField(max_length=128, unique=True)
    step_order = models.PositiveIntegerField()
    step_name = models.CharField(max_length=255)
    operation_id = models.CharField(max_length=128, null=True, blank=True)
    input_bindings = models.JSONField(default=list)
    expected_bindings = models.JSONField(default=list)
    assertion_ids = models.JSONField(default=list)
    retry_policy = models.JSONField(default=dict)
    optional = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["step_order", "id"]

    def __str__(self) -> str:
        """返回便于后台查看的步骤标识。"""
        return f"{self.scenario.scenario_code}#{self.step_order}"


class ScenarioReviewRecord(models.Model):
    """场景审核留痕记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="reviews", on_delete=models.CASCADE)
    review_id = models.CharField(max_length=128, unique=True)
    reviewer = models.CharField(max_length=128)
    review_comment = models.TextField(null=True, blank=True)
    review_status = models.CharField(max_length=32)
    reviewed_at = models.DateTimeField()
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["reviewed_at", "id"]


class ScenarioExecutionRecord(models.Model):
    """场景执行请求与结果记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="executions", on_delete=models.CASCADE)
    execution_id = models.CharField(max_length=128, unique=True)
    execution_status = models.CharField(max_length=32, default="not_started")
    passed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    report_path = models.CharField(max_length=255, null=True, blank=True)
    failure_summary = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
