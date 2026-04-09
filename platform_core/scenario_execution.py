"""V2 场景执行闭环流水线。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from platform_core.assets import AssetWorkspace
from platform_core.executors import PytestExecutor
from platform_core.models import AssetManifest, ExecutionRecord, GenerationRecord, SourceDocument
from platform_core.renderers import TemplateRenderer
from platform_core.rules import RuleValidator


@dataclass(frozen=True)
class PublicBaselineOperationBinding:
    """公开基线操作绑定定义。"""

    operation_id: str
    http_method: str
    path_template: str
    path_param_names: tuple[str, ...] = ()
    query_param_names: tuple[str, ...] = ()


@dataclass
class ScenarioExecutionPipelineResult:
    """场景执行流水线的最小输出。"""

    source_document: SourceDocument
    execution_record: ExecutionRecord
    generation_records: list[GenerationRecord]
    asset_manifest: AssetManifest
    asset_manifest_path: str
    generated_paths: dict[str, str]


class ScenarioExecutionBindingError(ValueError):
    """场景步骤缺少可执行绑定时抛出的异常。"""


class ScenarioExecutionPipeline:
    """把已确认场景导出为 pytest 工作区并执行。"""

    PUBLIC_BASE_URL = "https://jsonplaceholder.typicode.com"
    SUPPORTED_OPERATIONS: dict[str, PublicBaselineOperationBinding] = {
        "operation-get-user": PublicBaselineOperationBinding(
            operation_id="operation-get-user",
            http_method="GET",
            path_template="/users/{user_id}",
            path_param_names=("user_id",),
        ),
        "operation-list-user-todos": PublicBaselineOperationBinding(
            operation_id="operation-list-user-todos",
            http_method="GET",
            path_template="/users/{user_id}/todos",
            path_param_names=("user_id",),
        ),
    }

    def __init__(
        self,
        project_root: str | Path | None = None,
        renderer: TemplateRenderer | None = None,
        validator: RuleValidator | None = None,
        executor: PytestExecutor | None = None,
    ) -> None:
        """装配模板渲染、规则校验和 pytest 执行能力。"""
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.renderer = renderer or TemplateRenderer()
        self.validator = validator or RuleValidator()
        self.executor = executor or PytestExecutor(project_root=self.project_root)

    def run(
        self,
        scenario: Any,
        steps: list[Any],
        output_root: str | Path,
    ) -> ScenarioExecutionPipelineResult:
        """执行场景导出、pytest 运行和结果清单落盘。"""
        asset_workspace = AssetWorkspace(output_root)
        asset_workspace.prepare()

        normalized_steps = self._normalize_steps(steps)
        test_path = asset_workspace.tests_dir / f"test_{scenario.scenario_code}.py"
        violations = self.validator.validate_test_file_name(test_path.name)
        if violations:
            raise ValueError("; ".join(violations))

        rendered_test_module = self.renderer.render_scenario_test_module(
            scenario_code=scenario.scenario_code,
            scenario_name=scenario.scenario_name,
            base_url=self.PUBLIC_BASE_URL,
            steps=normalized_steps,
        )
        test_path.write_text(rendered_test_module, encoding="utf-8")

        source_document = self._build_source_document(scenario)
        test_digest = asset_workspace.build_content_digest(test_path)
        generation_record = self._write_generation_record(
            records_dir=asset_workspace.records_dir,
            source_id=source_document.source_id,
            asset_path=test_path,
            scenario=scenario,
            target_asset_digest=test_digest,
        )
        execution_record = self.executor.run(
            test_path=test_path,
            output_root=asset_workspace.workspace_root,
            target_id=scenario.scenario_code,
        )
        generation_record.execution_status = "passed" if execution_record.result_status == "passed" else "failed"
        generation_record_path = asset_workspace.records_dir / f"{generation_record.generation_id}.json"
        generation_record_path.write_text(
            self.renderer.render_generation_record(generation_record),
            encoding="utf-8",
        )

        generated_asset = asset_workspace.build_asset_record(
            asset_type="test_case",
            asset_path=test_path,
            generation_record=generation_record,
            module_code=scenario.module_id,
            operation_code=scenario.scenario_code,
            content_digest=test_digest,
        )
        execution_record_path = asset_workspace.records_dir / "execution_record.json"
        execution_record_path.write_text(
            json.dumps(execution_record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        asset_manifest, asset_manifest_path = asset_workspace.write_manifest(
            source_document=source_document,
            assets=[generated_asset],
            generation_records=[generation_record],
            execution_record=execution_record,
        )
        return ScenarioExecutionPipelineResult(
            source_document=source_document,
            execution_record=execution_record,
            generation_records=[generation_record],
            asset_manifest=asset_manifest,
            asset_manifest_path=str(asset_manifest_path),
            generated_paths={f"test::{scenario.scenario_code}": str(test_path)},
        )

    def _normalize_steps(self, steps: list[Any]) -> list[dict[str, Any]]:
        """把持久化步骤转换为模板可直接消费的结构。"""
        return [self._normalize_step(step) for step in steps]

    def _normalize_step(self, step: Any) -> list[dict[str, Any]] | dict[str, Any]:
        """标准化单个步骤的请求和期望配置。"""
        binding = self._resolve_binding(step.operation_id)
        raw_step = step.metadata.get("raw_step") if isinstance(step.metadata, dict) else {}
        raw_step = raw_step or {}
        request_payload = self._merge_request_payload(raw_step=raw_step, binding=binding)
        expected = raw_step.get("expected") or {}
        missing_path_params = [
            param_name for param_name in binding.path_param_names if param_name not in request_payload["path_params"]
        ]
        if missing_path_params:
            raise ScenarioExecutionBindingError(
                f"步骤缺少必需路径参数: {step.step_name} -> {', '.join(missing_path_params)}"
            )
        return {
            "step_id": step.step_id,
            "step_order": step.step_order,
            "step_name": step.step_name,
            "operation_id": step.operation_id,
            "http_method": binding.http_method,
            "path_template": binding.path_template,
            "request": request_payload,
            "expected": {
                "status_code": int(expected.get("status_code", 200)),
                "extract": expected.get("extract") or {},
            },
        }

    @classmethod
    def _resolve_binding(cls, operation_id: str | None) -> PublicBaselineOperationBinding:
        """根据操作标识解析公开基线绑定。"""
        if not operation_id or operation_id not in cls.SUPPORTED_OPERATIONS:
            raise ScenarioExecutionBindingError(f"未绑定可执行的公开基线操作: {operation_id}")
        return cls.SUPPORTED_OPERATIONS[operation_id]

    @staticmethod
    def _merge_request_payload(
        raw_step: dict[str, Any],
        binding: PublicBaselineOperationBinding,
    ) -> dict[str, Any]:
        """合并原始请求配置与变量使用映射。"""
        request_payload = raw_step.get("request") or {}
        uses = raw_step.get("uses") or {}
        path_params = dict(request_payload.get("path_params") or {})
        query_params = dict(request_payload.get("query_params") or {})
        for param_name in binding.path_param_names:
            if param_name not in path_params and param_name in uses:
                path_params[param_name] = uses[param_name]
        for param_name in binding.query_param_names:
            if param_name not in query_params and param_name in uses:
                query_params[param_name] = uses[param_name]
        json_payload = request_payload.get("json")
        if json_payload is None and "body" in request_payload:
            json_payload = request_payload.get("body")
        return {
            "path_params": path_params,
            "query_params": query_params,
            "json": json_payload,
        }

    @staticmethod
    def _build_source_document(scenario: Any) -> SourceDocument:
        """根据数据库中的场景记录构造统一来源对象。"""
        raw_reference = None
        if scenario.source_ids:
            raw_reference = scenario.source_ids[0]
        return SourceDocument(
            source_id=scenario.source_ids[0] if scenario.source_ids else scenario.scenario_id,
            source_type="functional_case",
            source_name=scenario.scenario_name,
            source_path=f"scenario://{scenario.scenario_id}",
            source_summary=scenario.scenario_desc,
            imported_at=getattr(scenario, "created_at", datetime.now(UTC)),
            imported_by="codex",
            raw_reference=raw_reference or scenario.scenario_id,
        )

    def _write_generation_record(
        self,
        records_dir: Path,
        source_id: str,
        asset_path: Path,
        scenario: Any,
        target_asset_digest: str,
    ) -> GenerationRecord:
        """为场景测试文件写出生成记录。"""
        record = GenerationRecord(
            generation_id=f"gen-{uuid4().hex[:8]}",
            generation_type="scenario",
            source_ids=[source_id],
            target_asset_type="test_case",
            target_asset_path=str(asset_path),
            generator_type="hybrid",
            generated_at=datetime.now(UTC),
            generated_by="codex",
            generation_version="v2",
            template_reference="templates/tests/test_scenario_module.py.j2",
            module_code=scenario.module_id,
            operation_code=scenario.scenario_code,
            target_asset_digest=target_asset_digest,
            review_status=scenario.review_status,
            execution_status="not_run",
        )
        violations = self.validator.validate_generation_record(record)
        if violations:
            raise ValueError("; ".join(violations))
        record_path = records_dir / f"{record.generation_id}.json"
        record_path.write_text(self.renderer.render_generation_record(record), encoding="utf-8")
        return record


__all__ = [
    "PublicBaselineOperationBinding",
    "ScenarioExecutionBindingError",
    "ScenarioExecutionPipeline",
    "ScenarioExecutionPipelineResult",
]
