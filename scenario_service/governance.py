"""V3 P0 治理引导与上下文解析服务。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from django.db import transaction

from scenario_service.models import (
    BaselineVersionRecord,
    GovernanceMigrationRecord,
    ProjectRecord,
    ScenarioExecutionRecord,
    ScenarioRecord,
    ScenarioSetRecord,
    TestEnvironmentRecord,
)


@dataclass(slots=True)
class GovernanceContext:
    """治理上下文聚合对象。"""

    project: ProjectRecord
    environment: TestEnvironmentRecord
    scenario_set: ScenarioSetRecord
    baseline_version: BaselineVersionRecord


class GovernanceBootstrapService:
    """负责默认项目迁移和治理上下文解析。"""

    DEFAULT_PROJECT_ID = "project-default"
    DEFAULT_PROJECT_CODE = "default-project"
    DEFAULT_PROJECT_NAME = "默认项目"
    DEFAULT_ENVIRONMENT_ID = "env-default"
    DEFAULT_ENVIRONMENT_CODE = "default-env"
    DEFAULT_ENVIRONMENT_NAME = "默认环境"
    DEFAULT_SCENARIO_SET_ID = "scenario-set-default"
    DEFAULT_SCENARIO_SET_CODE = "default-scenario-set"
    DEFAULT_SCENARIO_SET_NAME = "默认场景集"
    DEFAULT_BASELINE_VERSION_ID = "baseline-version-default-v1"
    DEFAULT_BASELINE_VERSION_CODE = "baseline-v1"
    DEFAULT_BASELINE_VERSION_NAME = "默认基线 V1"

    @transaction.atomic
    def ensure_bootstrap(self) -> GovernanceContext:
        """确保默认治理对象存在，并为历史资产补齐默认归属。"""
        context = self.resolve_context()
        self._backfill_default_context(context=context)
        return context

    @transaction.atomic
    def resolve_context(
        self,
        *,
        project_code: str | None = None,
        environment_code: str | None = None,
        scenario_set_code: str | None = None,
    ) -> GovernanceContext:
        """解析或创建治理上下文。"""
        resolved_project_code = project_code or self.DEFAULT_PROJECT_CODE
        project = self._get_or_create_project(project_code=resolved_project_code)

        resolved_environment_code = environment_code or self.DEFAULT_ENVIRONMENT_CODE
        environment = self._get_or_create_environment(
            project=project,
            environment_code=resolved_environment_code,
            is_default=resolved_environment_code == self.DEFAULT_ENVIRONMENT_CODE,
        )

        resolved_scenario_set_code = scenario_set_code or self.DEFAULT_SCENARIO_SET_CODE
        scenario_set = self._get_or_create_scenario_set(
            project=project,
            scenario_set_code=resolved_scenario_set_code,
        )
        baseline_version = self._get_or_create_active_baseline_version(scenario_set=scenario_set)
        return GovernanceContext(
            project=project,
            environment=environment,
            scenario_set=scenario_set,
            baseline_version=baseline_version,
        )

    @transaction.atomic
    def activate_baseline_version(
        self,
        *,
        project_code: str,
        scenario_set_code: str,
        version_code: str,
        version_name: str | None = None,
    ) -> GovernanceContext:
        """切换指定场景集的当前生效版本。"""
        context = self.resolve_context(
            project_code=project_code,
            scenario_set_code=scenario_set_code,
        )
        context.scenario_set.baseline_versions.update(is_active=False)
        baseline_version, _ = BaselineVersionRecord.objects.get_or_create(
            scenario_set=context.scenario_set,
            version_code=version_code,
            defaults={
                "baseline_version_id": f"baseline-version-{project_code}-{scenario_set_code}-{version_code}",
                "version_name": version_name or self._prettify_name(version_code),
                "is_frozen": True,
                "is_active": True,
                "metadata": {},
            },
        )
        baseline_version.is_active = True
        baseline_version.version_name = version_name or baseline_version.version_name
        baseline_version.is_frozen = True
        baseline_version.save(update_fields=["is_active", "version_name", "is_frozen", "updated_at"])
        return GovernanceContext(
            project=context.project,
            environment=context.environment,
            scenario_set=context.scenario_set,
            baseline_version=baseline_version,
        )

    def build_context_summary(self, context: GovernanceContext) -> dict:
        """构造单个治理上下文摘要。"""
        return {
            "project": self.build_project_summary(context.project),
            "environment": self.build_environment_summary(context.environment),
            "scenario_set": self.build_scenario_set_summary(context.scenario_set),
            "baseline_version": self.build_baseline_version_summary(context.baseline_version),
        }

    def build_context_tree(self) -> dict:
        """构造治理入口使用的上下文树。"""
        self.ensure_bootstrap()
        projects = []
        for project in ProjectRecord.objects.all().order_by("project_code", "id"):
            environments = [
                self.build_environment_summary(environment)
                for environment in project.environments.all().order_by("-is_default", "environment_code", "id")
            ]
            scenario_sets = []
            for scenario_set in project.scenario_sets.all().order_by("scenario_set_code", "id"):
                active_version = self.get_active_baseline_version(scenario_set=scenario_set)
                scenario_sets.append(
                    {
                        **self.build_scenario_set_summary(scenario_set),
                        "active_version": self.build_baseline_version_summary(active_version) if active_version else None,
                        "versions": [
                            self.build_baseline_version_summary(version)
                            for version in scenario_set.baseline_versions.all().order_by("-is_active", "version_code", "id")
                        ],
                    }
                )
            projects.append(
                {
                    **self.build_project_summary(project),
                    "environments": environments,
                    "scenario_sets": scenario_sets,
                }
            )
        return {
            "projects": projects,
            "migration_status": self.get_migration_status_summary(),
        }

    def get_migration_status_summary(self) -> dict:
        """返回默认项目迁移状态摘要。"""
        latest = GovernanceMigrationRecord.objects.order_by("-executed_at", "-id").first()
        unassigned_scenarios = ScenarioRecord.objects.filter(project__isnull=True).count()
        unassigned_executions = ScenarioExecutionRecord.objects.filter(project__isnull=True).count()
        return {
            "latest_migration_id": latest.migration_id if latest else "",
            "status": latest.status if latest else "not_started",
            "migrated_scenario_count": latest.migrated_scenario_count if latest else 0,
            "migrated_execution_count": latest.migrated_execution_count if latest else 0,
            "failed_entity_count": latest.failed_entity_count if latest else 0,
            "remaining_unassigned_scenarios": unassigned_scenarios,
            "remaining_unassigned_executions": unassigned_executions,
        }

    def build_project_summary(self, project: ProjectRecord) -> dict:
        """构造项目摘要。"""
        return {
            "project_id": project.project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "lifecycle_status": project.lifecycle_status,
            "is_archived": project.is_archived,
        }

    def build_environment_summary(self, environment: TestEnvironmentRecord) -> dict:
        """构造环境摘要。"""
        return {
            "environment_id": environment.environment_id,
            "environment_code": environment.environment_code,
            "environment_name": environment.environment_name,
            "base_url": environment.base_url,
            "isolation_key": environment.isolation_key,
            "is_default": environment.is_default,
        }

    def build_scenario_set_summary(self, scenario_set: ScenarioSetRecord) -> dict:
        """构造场景集摘要。"""
        return {
            "scenario_set_id": scenario_set.scenario_set_id,
            "scenario_set_code": scenario_set.scenario_set_code,
            "scenario_set_name": scenario_set.scenario_set_name,
            "tags": scenario_set.tags,
            "is_archived": scenario_set.is_archived,
        }

    def build_baseline_version_summary(self, baseline_version: BaselineVersionRecord) -> dict:
        """构造基线版本摘要。"""
        return {
            "baseline_version_id": baseline_version.baseline_version_id,
            "version_code": baseline_version.version_code,
            "version_name": baseline_version.version_name,
            "is_frozen": baseline_version.is_frozen,
            "is_active": baseline_version.is_active,
        }

    def get_active_baseline_version(self, *, scenario_set: ScenarioSetRecord) -> BaselineVersionRecord | None:
        """加载场景集当前生效版本。"""
        return scenario_set.baseline_versions.filter(is_active=True).order_by("-updated_at", "-id").first()

    def build_project_scoped_scenario_id(self, *, project_code: str, scenario_id: str) -> str:
        """为跨项目同名场景构造稳定存储标识。"""
        if project_code == self.DEFAULT_PROJECT_CODE:
            return scenario_id
        normalized_project_code = project_code.replace("_", "-")
        if scenario_id.startswith("scenario-"):
            return f"scenario-{normalized_project_code}-{scenario_id.removeprefix('scenario-')}"
        return f"scenario-{normalized_project_code}-{scenario_id}"

    def build_project_scoped_step_id(self, *, project_code: str, step_id: str) -> str:
        """为跨项目步骤构造稳定存储标识。"""
        if project_code == self.DEFAULT_PROJECT_CODE:
            return step_id
        normalized_project_code = project_code.replace("_", "-")
        return f"{normalized_project_code}-{step_id}"

    def resolve_execution_context(
        self,
        *,
        scenario: ScenarioRecord,
        project_code: str,
        environment_code: str,
    ) -> GovernanceContext:
        """校验执行请求中的项目和环境是否与场景归属一致。"""
        if scenario.project is None or scenario.project.project_code != project_code:
            raise ValueError("project_context_mismatch")
        if scenario.environment is None or scenario.environment.environment_code != environment_code:
            raise ValueError("environment_context_mismatch")
        scenario_set = scenario.scenario_set or self.resolve_context(project_code=project_code).scenario_set
        baseline_version = self.get_active_baseline_version(scenario_set=scenario_set)
        if baseline_version is None:
            baseline_version = self._get_or_create_active_baseline_version(scenario_set=scenario_set)
        return GovernanceContext(
            project=scenario.project,
            environment=scenario.environment,
            scenario_set=scenario_set,
            baseline_version=baseline_version,
        )

    def resolve_export_context(self, *, scenario: ScenarioRecord, project_code: str) -> GovernanceContext:
        """校验导出请求的项目归属，并补齐当前活动版本上下文。"""
        if scenario.project is None or scenario.project.project_code != project_code:
            raise ValueError("project_context_mismatch")
        environment = scenario.environment
        scenario_set = scenario.scenario_set
        if environment is None or scenario_set is None:
            resolved = self.resolve_context(
                project_code=project_code,
                environment_code=environment.environment_code if environment else None,
                scenario_set_code=scenario_set.scenario_set_code if scenario_set else None,
            )
            environment = environment or resolved.environment
            scenario_set = scenario_set or resolved.scenario_set
        baseline_version = self.get_active_baseline_version(scenario_set=scenario_set)
        if baseline_version is None:
            baseline_version = self._get_or_create_active_baseline_version(scenario_set=scenario_set)
        return GovernanceContext(
            project=scenario.project,
            environment=environment,
            scenario_set=scenario_set,
            baseline_version=baseline_version,
        )

    def build_workspace_root(self, *, context: GovernanceContext, scenario: ScenarioRecord) -> Path:
        """按项目、环境和场景集生成默认执行工作区根目录。"""
        root = (
            Path(__file__).resolve().parent.parent
            / "report"
            / "scenario_workspaces"
            / self._normalize_code_fragment(context.project.project_code)
            / self._normalize_code_fragment(context.environment.environment_code)
            / self._normalize_code_fragment(context.scenario_set.scenario_set_code)
        )
        return root / f"{self._normalize_code_fragment(scenario.scenario_code)}_{uuid4().hex[:8]}"

    def build_export_path(
        self,
        *,
        context: GovernanceContext,
        scenario: ScenarioRecord,
        export_root: Path | None = None,
    ) -> Path:
        """按项目归属生成场景导出文件路径。"""
        root = export_root or (Path(__file__).resolve().parent.parent / "report" / "scenario_exports")
        root = (
            root
            / self._normalize_code_fragment(context.project.project_code)
            / self._normalize_code_fragment(context.environment.environment_code)
            / self._normalize_code_fragment(context.scenario_set.scenario_set_code)
        )
        return root / f"{self._normalize_code_fragment(scenario.scenario_id)}.json"

    def _backfill_default_context(self, *, context: GovernanceContext) -> None:
        """为历史场景与执行记录回填默认项目归属。"""
        migrated_scenario_count = ScenarioRecord.objects.filter(project__isnull=True).update(
            project=context.project,
            environment=context.environment,
            scenario_set=context.scenario_set,
        )
        migrated_execution_count = ScenarioExecutionRecord.objects.filter(project__isnull=True).update(
            project=context.project,
            environment=context.environment,
            scenario_set=context.scenario_set,
            baseline_version=context.baseline_version,
        )
        latest = GovernanceMigrationRecord.objects.order_by("-executed_at", "-id").first()
        if migrated_scenario_count == 0 and migrated_execution_count == 0 and latest:
            return
        GovernanceMigrationRecord.objects.create(
            migration_id=f"migration-{uuid4().hex[:12]}",
            migration_name="default_project_bootstrap",
            migration_scope="default_project_bootstrap",
            status="completed",
            migrated_scenario_count=migrated_scenario_count,
            migrated_execution_count=migrated_execution_count,
            failed_entity_count=0,
            metadata={
                "project_code": context.project.project_code,
                "environment_code": context.environment.environment_code,
                "scenario_set_code": context.scenario_set.scenario_set_code,
                "version_code": context.baseline_version.version_code,
            },
        )

    def _get_or_create_project(self, *, project_code: str) -> ProjectRecord:
        """按编码加载或创建项目。"""
        defaults = {
            "project_id": f"project-{project_code}",
            "project_name": self.DEFAULT_PROJECT_NAME if project_code == self.DEFAULT_PROJECT_CODE else self._prettify_name(project_code),
            "lifecycle_status": "active",
            "is_archived": False,
            "metadata": {},
        }
        project, _ = ProjectRecord.objects.get_or_create(project_code=project_code, defaults=defaults)
        return project

    def _get_or_create_environment(
        self,
        *,
        project: ProjectRecord,
        environment_code: str,
        is_default: bool,
    ) -> TestEnvironmentRecord:
        """按编码加载或创建环境。"""
        defaults = {
            "environment_id": f"environment-{project.project_code}-{environment_code}",
            "environment_name": self.DEFAULT_ENVIRONMENT_NAME if environment_code == self.DEFAULT_ENVIRONMENT_CODE else self._prettify_name(environment_code),
            "base_url": "https://jsonplaceholder.typicode.com" if environment_code == self.DEFAULT_ENVIRONMENT_CODE else "",
            "auth_config": {},
            "request_headers": {},
            "variable_set": {},
            "proxy_config": {},
            "timeout_seconds": 30,
            "isolation_key": f"{project.project_code}:{environment_code}",
            "is_default": is_default,
            "metadata": {},
        }
        environment, created = TestEnvironmentRecord.objects.get_or_create(
            project=project,
            environment_code=environment_code,
            defaults=defaults,
        )
        if not created and is_default and not environment.is_default:
            environment.is_default = True
            environment.save(update_fields=["is_default", "updated_at"])
        return environment

    def _get_or_create_scenario_set(self, *, project: ProjectRecord, scenario_set_code: str) -> ScenarioSetRecord:
        """按编码加载或创建场景集。"""
        defaults = {
            "scenario_set_id": f"scenario-set-{project.project_code}-{scenario_set_code}",
            "scenario_set_name": self.DEFAULT_SCENARIO_SET_NAME
            if scenario_set_code == self.DEFAULT_SCENARIO_SET_CODE
            else self._prettify_name(scenario_set_code),
            "description": "",
            "tags": [],
            "is_archived": False,
            "metadata": {},
        }
        scenario_set, _ = ScenarioSetRecord.objects.get_or_create(
            project=project,
            scenario_set_code=scenario_set_code,
            defaults=defaults,
        )
        return scenario_set

    def _get_or_create_active_baseline_version(self, *, scenario_set: ScenarioSetRecord) -> BaselineVersionRecord:
        """为场景集确保存在当前生效版本。"""
        active_version = self.get_active_baseline_version(scenario_set=scenario_set)
        if active_version is not None:
            return active_version
        baseline_version_id = (
            self.DEFAULT_BASELINE_VERSION_ID
            if scenario_set.project.project_code == self.DEFAULT_PROJECT_CODE
            and scenario_set.scenario_set_code == self.DEFAULT_SCENARIO_SET_CODE
            else f"baseline-version-{scenario_set.project.project_code}-{scenario_set.scenario_set_code}-{self.DEFAULT_BASELINE_VERSION_CODE}"
        )
        baseline_version, _ = BaselineVersionRecord.objects.get_or_create(
            scenario_set=scenario_set,
            version_code=self.DEFAULT_BASELINE_VERSION_CODE,
            defaults={
                "baseline_version_id": baseline_version_id,
                "version_name": self.DEFAULT_BASELINE_VERSION_NAME
                if scenario_set.scenario_set_code == self.DEFAULT_SCENARIO_SET_CODE
                else f"{self._prettify_name(scenario_set.scenario_set_code)} 基线 V1",
                "is_frozen": True,
                "is_active": True,
                "metadata": {},
            },
        )
        if not baseline_version.is_active:
            baseline_version.is_active = True
            baseline_version.is_frozen = True
            baseline_version.save(update_fields=["is_active", "is_frozen", "updated_at"])
        return baseline_version

    @staticmethod
    def _prettify_name(code: str) -> str:
        """把编码转换为可读名称。"""
        return code.replace("-", " ").replace("_", " ").strip().title() or code

    @staticmethod
    def _normalize_code_fragment(code: str) -> str:
        """把编码转换为适合目录和文件命名的稳定片段。"""
        return code.replace("\\", "-").replace("/", "-").replace(":", "-").strip() or "default"
