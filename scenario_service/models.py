"""V2 场景服务持久化模型。"""

from __future__ import annotations

from django.db import models


class ProjectRecord(models.Model):
    """项目治理根对象。"""

    project_id = models.CharField(max_length=128, unique=True)
    project_code = models.CharField(max_length=128, unique=True)
    project_name = models.CharField(max_length=255)
    lifecycle_status = models.CharField(max_length=32, default="active")
    is_archived = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["project_code", "id"]

    def __str__(self) -> str:
        """返回便于后台查看的项目标识。"""
        return f"{self.project_code}({self.lifecycle_status})"


class TestEnvironmentRecord(models.Model):
    """测试环境治理对象。"""

    __test__ = False

    environment_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="environments", on_delete=models.CASCADE)
    environment_code = models.CharField(max_length=128)
    environment_name = models.CharField(max_length=255)
    base_url = models.CharField(max_length=255, blank=True, default="")
    auth_config = models.JSONField(default=dict)
    request_headers = models.JSONField(default=dict)
    variable_set = models.JSONField(default=dict)
    proxy_config = models.JSONField(default=dict)
    timeout_seconds = models.PositiveIntegerField(default=30)
    isolation_key = models.CharField(max_length=128, blank=True, default="")
    is_default = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["project__project_code", "environment_code", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "environment_code"], name="uniq_project_environment_code"),
        ]

    def __str__(self) -> str:
        """返回便于后台查看的环境标识。"""
        return f"{self.project.project_code}/{self.environment_code}"


class ScenarioSetRecord(models.Model):
    """场景集治理对象。"""

    scenario_set_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="scenario_sets", on_delete=models.CASCADE)
    scenario_set_code = models.CharField(max_length=128)
    scenario_set_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list)
    is_archived = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["project__project_code", "scenario_set_code", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "scenario_set_code"], name="uniq_project_scenario_set_code"),
        ]

    def __str__(self) -> str:
        """返回便于后台查看的场景集标识。"""
        return f"{self.project.project_code}/{self.scenario_set_code}"


class BaselineVersionRecord(models.Model):
    """场景集基线版本治理对象。"""

    baseline_version_id = models.CharField(max_length=128, unique=True)
    scenario_set = models.ForeignKey(ScenarioSetRecord, related_name="baseline_versions", on_delete=models.CASCADE)
    version_code = models.CharField(max_length=128)
    version_name = models.CharField(max_length=255)
    is_frozen = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scenario_set__scenario_set_code", "-is_active", "version_code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["scenario_set", "version_code"],
                name="uniq_scenario_set_baseline_version_code",
            ),
        ]

    def __str__(self) -> str:
        """返回便于后台查看的基线版本标识。"""
        return f"{self.scenario_set.scenario_set_code}/{self.version_code}"


class GovernanceMigrationRecord(models.Model):
    """默认项目迁移与治理引导记录。"""

    migration_id = models.CharField(max_length=128, unique=True)
    migration_name = models.CharField(max_length=128)
    migration_scope = models.CharField(max_length=64, default="default_project_bootstrap")
    status = models.CharField(max_length=32, default="completed")
    migrated_scenario_count = models.PositiveIntegerField(default=0)
    migrated_execution_count = models.PositiveIntegerField(default=0)
    failed_entity_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict)
    executed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-executed_at", "-id"]


class ProjectRoleAssignmentRecord(models.Model):
    """项目成员角色授权记录。"""

    assignment_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="role_assignments", on_delete=models.CASCADE)
    subject_name = models.CharField(max_length=128)
    role_code = models.CharField(max_length=32)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_execute = models.BooleanField(default=False)
    can_review = models.BooleanField(default=False)
    can_schedule = models.BooleanField(default=False)
    can_grant = models.BooleanField(default=False)
    granted_by = models.CharField(max_length=128, default="system")
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["project__project_code", "subject_name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "subject_name"], name="uniq_project_role_assignment_subject"),
        ]

    def __str__(self) -> str:
        """返回便于后台查看的项目成员角色标识。"""
        return f"{self.project.project_code}/{self.subject_name}({self.role_code})"


class TrafficCaptureFormalizationRecord(models.Model):
    """抓包场景正式执行治理对象。"""

    confirmation_id = models.CharField(max_length=128, unique=True)
    scenario = models.OneToOneField(
        "ScenarioRecord",
        related_name="traffic_capture_formalization",
        on_delete=models.CASCADE,
    )
    project = models.ForeignKey(
        ProjectRecord,
        related_name="traffic_capture_formalizations",
        on_delete=models.PROTECT,
    )
    environment = models.ForeignKey(
        TestEnvironmentRecord,
        related_name="traffic_capture_formalizations",
        on_delete=models.PROTECT,
    )
    confirmation_status = models.CharField(max_length=32, default="draft")
    binding_status = models.CharField(max_length=32, default="pending")
    execution_readiness = models.CharField(max_length=32, default="blocked")
    confirmed_by = models.CharField(max_length=128, blank=True, default="")
    bindings_confirmed_by = models.CharField(max_length=128, blank=True, default="")
    last_execution_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["project__project_code", "scenario__scenario_code", "id"]

    def __str__(self) -> str:
        """返回便于后台查看的抓包正式执行对象标识。"""
        return f"{self.project.project_code}/{self.scenario.scenario_code}({self.execution_readiness})"


class ScenarioRecord(models.Model):
    """场景草稿与正式场景的持久化记录。"""

    scenario_id = models.CharField(max_length=128, unique=True)
    scenario_code = models.CharField(max_length=128)
    scenario_name = models.CharField(max_length=255)
    project = models.ForeignKey(ProjectRecord, related_name="scenarios", on_delete=models.PROTECT, null=True, blank=True)
    environment = models.ForeignKey(
        TestEnvironmentRecord,
        related_name="scenarios",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    scenario_set = models.ForeignKey(
        ScenarioSetRecord,
        related_name="scenarios",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
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


class ScenarioRevisionRecord(models.Model):
    """场景结构化修订留痕记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="revisions", on_delete=models.CASCADE)
    revision_id = models.CharField(max_length=128, unique=True)
    reviser = models.CharField(max_length=128)
    revision_comment = models.TextField(null=True, blank=True)
    applied_changes = models.JSONField(default=dict)
    revised_at = models.DateTimeField()
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["revised_at", "id"]


class ScenarioSourceRecord(models.Model):
    """场景来源追溯记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="sources", on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=32, default="scenario")
    entity_id = models.CharField(max_length=128, blank=True, default="")
    source_type = models.CharField(max_length=32)
    source_ref = models.CharField(max_length=255)
    confidence = models.CharField(max_length=16, default="high")
    issue_tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["id"]


class ScenarioSuggestionRecord(models.Model):
    """场景建议记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="suggestions", on_delete=models.CASCADE)
    suggestion_id = models.CharField(max_length=128, unique=True)
    suggestion_type = models.CharField(max_length=64)
    target_type = models.CharField(max_length=32)
    target_id = models.CharField(max_length=128, blank=True, default="")
    baseline_revision_id = models.CharField(max_length=128, blank=True, default="")
    patch_payload = models.JSONField(default=dict)
    diff_summary = models.JSONField(default=dict)
    confidence = models.CharField(max_length=16, default="medium")
    apply_status = models.CharField(max_length=32, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class ScenarioExecutionRecord(models.Model):
    """场景执行请求与结果记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="executions", on_delete=models.CASCADE)
    project = models.ForeignKey(ProjectRecord, related_name="executions", on_delete=models.PROTECT, null=True, blank=True)
    environment = models.ForeignKey(
        TestEnvironmentRecord,
        related_name="executions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    scenario_set = models.ForeignKey(
        ScenarioSetRecord,
        related_name="executions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    baseline_version = models.ForeignKey(
        BaselineVersionRecord,
        related_name="executions",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    execution_id = models.CharField(max_length=128, unique=True)
    execution_status = models.CharField(max_length=32, default="not_started")
    passed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    workspace_root = models.CharField(max_length=255, null=True, blank=True)
    report_path = models.CharField(max_length=255, null=True, blank=True)
    failure_summary = models.TextField(null=True, blank=True)
    trigger_source = models.CharField(max_length=32, default="manual")
    based_on_revision_id = models.CharField(max_length=128, null=True, blank=True)
    based_on_suggestion_id = models.CharField(max_length=128, null=True, blank=True)
    change_summary = models.JSONField(default=dict)
    diff_summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class ScenarioAuditLogRecord(models.Model):
    """关键治理动作审计日志记录。"""

    audit_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="audit_logs", on_delete=models.PROTECT, null=True, blank=True)
    scenario = models.ForeignKey(
        "ScenarioRecord",
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    execution = models.ForeignKey(
        "ScenarioExecutionRecord",
        related_name="audit_logs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    actor_name = models.CharField(max_length=128)
    action_type = models.CharField(max_length=64)
    action_result = models.CharField(max_length=32)
    target_type = models.CharField(max_length=32, default="scenario")
    target_id = models.CharField(max_length=128, blank=True, default="")
    detail_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        """返回便于后台查看的审计日志标识。"""
        return f"{self.action_type}/{self.actor_name}({self.action_result})"
