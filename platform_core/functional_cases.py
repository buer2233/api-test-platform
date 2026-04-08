"""功能测试用例驱动的场景草稿解析能力。"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from platform_core.models import (
    AssertionCandidate,
    DependencyLink,
    FunctionalCaseDraft,
    FunctionalCaseIssue,
    ScenarioLifecycleStatus,
    ScenarioStep,
    SourceDocument,
    TestScenario,
    VariableBinding,
)


class FunctionalCaseDraftParser:
    """把结构化功能测试用例输入解析为 V2 场景草稿。"""

    def parse(self, source_path: str | Path) -> FunctionalCaseDraft:
        """读取 JSON 功能测试用例并生成场景草稿聚合对象。"""
        source = Path(source_path)
        raw_case = json.loads(source.read_text(encoding="utf-8-sig"))
        return self.parse_payload(raw_case=raw_case, source_name=source.stem, source_path=source)

    def parse_payload(
        self,
        raw_case: dict[str, Any],
        source_name: str | None = None,
        source_path: Path | None = None,
    ) -> FunctionalCaseDraft:
        """直接把功能测试用例请求体解析为场景草稿聚合对象。"""
        resolved_source_name = source_name or raw_case.get("case_code") or raw_case.get("case_id") or "functional_case"
        source = source_path or Path(f"{self._normalize_identifier(resolved_source_name)}.json")
        source_document = self._build_source_document(source=source, raw_case=raw_case)
        scenario = self._build_scenario(raw_case=raw_case, source_document=source_document)

        steps: list[ScenarioStep] = []
        bindings: list[VariableBinding] = []
        dependencies: list[DependencyLink] = []
        assertions: list[AssertionCandidate] = []
        issues: list[FunctionalCaseIssue] = []
        binding_index: dict[str, VariableBinding] = {}

        for step_order, step_data in enumerate(raw_case.get("steps") or [], start=1):
            step = self._build_step(
                scenario=scenario,
                step_data=step_data,
                step_order=step_order,
            )
            steps.append(step)
            issues.extend(self._collect_step_issues(step=step))

            step_assertions = self._build_assertions(step=step, step_data=step_data)
            assertions.extend(step_assertions)
            step.assertion_ids = [assertion.assertion_id for assertion in step_assertions]

            step_bindings = self._build_bindings(step=step, step_data=step_data)
            for binding in step_bindings:
                binding_index[binding.variable_name] = binding
            bindings.extend(step_bindings)

            step_dependencies, dependency_issues = self._build_dependencies(
                step=step,
                step_data=step_data,
                binding_index=binding_index,
            )
            dependencies.extend(step_dependencies)
            issues.extend(dependency_issues)

        lifecycle = ScenarioLifecycleStatus(
            review_status=scenario.review_status,
            execution_status="not_started",
            current_stage="draft",
        )
        return FunctionalCaseDraft(
            source_document=source_document,
            scenario=scenario,
            steps=steps,
            bindings=bindings,
            dependencies=dependencies,
            assertions=assertions,
            review_records=[],
            lifecycle=lifecycle,
            issues=issues,
        )

    def _build_source_document(self, source: Path, raw_case: dict[str, Any]) -> SourceDocument:
        """构造功能测试用例来源对象。"""
        source_key = raw_case.get("case_code") or raw_case.get("case_id") or source.stem
        raw_reference = str(source.resolve()) if source.exists() else str(source)
        return SourceDocument(
            source_id=f"source-{self._normalize_identifier(source_key)}",
            source_type="functional_case",
            source_name=raw_case.get("case_name") or source.stem,
            source_path=str(source),
            source_version=raw_case.get("case_version"),
            source_summary=raw_case.get("case_desc") or raw_case.get("objective"),
            imported_at=datetime.now(UTC),
            imported_by="codex",
            raw_reference=raw_reference,
        )

    def _build_scenario(self, raw_case: dict[str, Any], source_document: SourceDocument) -> TestScenario:
        """构造场景草稿对象。"""
        scenario_code = self._resolve_scenario_code(raw_case=raw_case)
        scenario_key = raw_case.get("case_id") or scenario_code
        priority = raw_case.get("priority")
        normalized_priority = priority if priority in {"high", "medium", "low"} else "medium"
        return TestScenario(
            scenario_id=f"scenario-{self._normalize_identifier(scenario_key)}",
            scenario_name=raw_case.get("case_name") or scenario_code,
            scenario_code=scenario_code,
            module_id=raw_case.get("module_id"),
            scenario_desc=raw_case.get("case_desc") or raw_case.get("objective"),
            source_ids=[source_document.source_id],
            priority=normalized_priority,
            review_status="pending",
            preconditions=list(raw_case.get("preconditions") or []),
            postconditions=list(raw_case.get("postconditions") or []),
            cleanup_required=bool(raw_case.get("cleanup_required", False)),
            metadata={"input_type": "functional_case_json"},
        )

    def _build_step(self, scenario: TestScenario, step_data: dict[str, Any], step_order: int) -> ScenarioStep:
        """构造单个场景步骤对象。"""
        step_name = step_data.get("step_name") or f"步骤{step_order}"
        step_key = step_data.get("step_code") or step_name or step_order
        expected = step_data.get("expected") or {}
        return ScenarioStep(
            step_id=f"{scenario.scenario_id}-step-{self._normalize_identifier(step_key)}-{step_order}",
            scenario_id=scenario.scenario_id,
            step_order=step_order,
            step_name=step_name,
            operation_id=step_data.get("operation_id"),
            input_bindings=list((step_data.get("uses") or {}).keys()),
            expected_bindings=list(expected.keys()),
            assertion_ids=[],
            retry_policy=step_data.get("retry_policy") or {},
            optional=bool(step_data.get("optional", False)),
            metadata={"raw_step": step_data},
        )

    def _collect_step_issues(self, step: ScenarioStep) -> list[FunctionalCaseIssue]:
        """收集单个步骤的结构化问题。"""
        if step.operation_id:
            return []
        return [
            FunctionalCaseIssue(
                issue_code="missing_operation_id",
                issue_message=f"步骤缺少 operation_id，当前步骤无法绑定既有接口资产: {step.step_name}",
                severity="error",
                step_id=step.step_id,
                step_order=step.step_order,
            )
        ]

    def _build_assertions(self, step: ScenarioStep, step_data: dict[str, Any]) -> list[AssertionCandidate]:
        """基于步骤期望生成最小断言候选。"""
        expected = step_data.get("expected") or {}
        status_code = expected.get("status_code")
        if status_code is None:
            return []
        return [
            AssertionCandidate(
                assertion_id=f"{step.step_id}-status-code",
                operation_id=step.operation_id,
                scenario_step_id=step.step_id,
                assertion_type="status_code",
                target_path="status_code",
                expected_value=status_code,
                priority="high",
                source="functional_case",
                confidence_score=1.0,
                review_status="pending",
            )
        ]

    def _build_bindings(self, step: ScenarioStep, step_data: dict[str, Any]) -> list[VariableBinding]:
        """基于提取配置生成变量绑定候选。"""
        expected = step_data.get("expected") or {}
        extract_map = expected.get("extract") or {}
        bindings: list[VariableBinding] = []
        for variable_name, source_field_path in extract_map.items():
            bindings.append(
                VariableBinding(
                    binding_id=f"{step.step_id}-binding-{self._normalize_identifier(variable_name)}",
                    variable_name=variable_name,
                    source_operation_id=step.operation_id,
                    source_field_path=source_field_path,
                    extract_expression=self._build_extract_expression(source_field_path),
                    target_operations=[],
                    target_scope="scenario",
                    fallback_value=None,
                    required=True,
                    metadata={"source_step_id": step.step_id},
                )
            )
        return bindings

    def _build_dependencies(
        self,
        step: ScenarioStep,
        step_data: dict[str, Any],
        binding_index: dict[str, VariableBinding],
    ) -> tuple[list[DependencyLink], list[FunctionalCaseIssue]]:
        """基于变量使用关系构造依赖候选与问题记录。"""
        dependencies: list[DependencyLink] = []
        issues: list[FunctionalCaseIssue] = []
        uses = step_data.get("uses") or {}
        for variable_name, reference in uses.items():
            binding = binding_index.get(variable_name)
            if binding is None:
                issues.append(
                    FunctionalCaseIssue(
                        issue_code="missing_binding_source",
                        issue_message=f"变量 {variable_name} 缺少上游提取来源，当前仅保留为待审核问题。",
                        severity="error",
                        step_id=step.step_id,
                        step_order=step.step_order,
                        metadata={"reference": reference},
                    )
                )
                continue
            if step.operation_id and step.operation_id not in binding.target_operations:
                binding.target_operations.append(step.operation_id)
            dependencies.append(
                DependencyLink(
                    dependency_id=f"{step.step_id}-dependency-{self._normalize_identifier(variable_name)}",
                    upstream_operation_id=binding.source_operation_id,
                    downstream_operation_id=step.operation_id,
                    dependency_type="data_flow",
                    binding_id=binding.binding_id,
                    required=True,
                    confidence_score=1.0,
                    source="functional_case",
                    metadata={"reference": reference},
                )
            )
        return dependencies, issues

    @staticmethod
    def _build_extract_expression(source_field_path: str | None) -> str | None:
        """把字段路径转换为统一的 JSONPath 风格表达式。"""
        if not source_field_path:
            return None
        normalized_path = str(source_field_path).lstrip("$.")
        return f"$.{normalized_path}"

    def _resolve_scenario_code(self, raw_case: dict[str, Any]) -> str:
        """解析场景编码，并在缺失时提供稳定回退值。"""
        candidate = raw_case.get("case_code") or raw_case.get("case_name") or raw_case.get("case_id") or "scenario"
        normalized = self._normalize_identifier(candidate)
        if normalized:
            return normalized
        fallback = raw_case.get("case_id") or "scenario"
        return self._normalize_identifier(fallback)

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        """把输入值标准化为可复用的 snake_case 标识。"""
        raw_value = str(value or "").strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", raw_value)
        return normalized.strip("_") or "item"


__all__ = ["FunctionalCaseDraftParser"]
