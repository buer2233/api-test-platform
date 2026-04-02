"""文档驱动最小闭环流水线。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from platform_core.assets import AssetWorkspace
from platform_core.executors import PytestExecutor
from platform_core.models import GenerationRecord, PipelineResult
from platform_core.parsers import OpenAPIDocumentParser
from platform_core.renderers import TemplateRenderer
from platform_core.rules import RuleValidator


class DocumentDrivenPipeline:
    """V1 文档驱动最小闭环服务。"""

    def __init__(
        self,
        project_root: str | Path | None = None,
        parser: OpenAPIDocumentParser | None = None,
        renderer: TemplateRenderer | None = None,
        validator: RuleValidator | None = None,
        executor: PytestExecutor | None = None,
    ) -> None:
        """初始化解析、渲染、规则校验和执行依赖。"""
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.parser = parser or OpenAPIDocumentParser()
        self.renderer = renderer or TemplateRenderer()
        self.validator = validator or RuleValidator()
        self.executor = executor or PytestExecutor(project_root=self.project_root)

    def run(self, source_path: str | Path, output_root: str | Path) -> PipelineResult:
        """执行完整的文档驱动闭环并返回流水线结果。"""
        parsed = self.parser.parse(source_path)
        asset_workspace = AssetWorkspace(output_root)
        asset_workspace.prepare()
        generated_paths: dict[str, str] = {}
        generation_records: list[GenerationRecord] = []
        generated_assets = []

        modules_by_id = {module.module_id: module for module in parsed.modules}
        operations_by_module: dict[str, list] = {}
        for operation in parsed.operations:
            operations_by_module.setdefault(operation.module_id, []).append(operation)

        for module_id, operations in operations_by_module.items():
            module = modules_by_id[module_id]
            api_path = asset_workspace.apis_dir / f"{module.module_code}_api.py"
            api_path.write_text(self.renderer.render_api_module(module, operations), encoding="utf-8")
            generated_paths[f"api::{module.module_code}"] = str(api_path)
            api_digest = asset_workspace.build_content_digest(api_path)
            api_record = self._write_generation_record(
                records_dir=asset_workspace.records_dir,
                source_id=parsed.source_document.source_id,
                asset_type="api_module",
                asset_path=api_path,
                template_reference="templates/api/api_module.py.j2",
                module_code=module.module_code,
                target_asset_digest=api_digest,
            )
            generation_records.append(api_record)
            generated_assets.append(
                asset_workspace.build_asset_record(
                    asset_type="api_module",
                    asset_path=api_path,
                    generation_record=api_record,
                    module_code=module.module_code,
                    content_digest=api_digest,
                )
            )

            for operation in operations:
                violations = self.validator.validate_operation(operation)
                test_path = asset_workspace.tests_dir / f"test_{operation.operation_code}.py"
                violations.extend(self.validator.validate_test_file_name(test_path.name))
                assertions = [
                    assertion for assertion in parsed.assertions if assertion.operation_id == operation.operation_id
                ]
                violations.extend(self.validator.validate_assertions(operation, assertions))
                if violations:
                    raise ValueError("; ".join(violations))
                test_path.write_text(
                    self.renderer.render_test_module(module, operation, assertions),
                    encoding="utf-8",
                )
                generated_paths[f"test::{operation.operation_code}"] = str(test_path)
                test_digest = asset_workspace.build_content_digest(test_path)
                test_record = self._write_generation_record(
                    records_dir=asset_workspace.records_dir,
                    source_id=parsed.source_document.source_id,
                    asset_type="test_case",
                    asset_path=test_path,
                    template_reference="templates/tests/test_module.py.j2",
                    module_code=module.module_code,
                    operation_code=operation.operation_code,
                    target_asset_digest=test_digest,
                )
                generation_records.append(test_record)
                generated_assets.append(
                    asset_workspace.build_asset_record(
                        asset_type="test_case",
                        asset_path=test_path,
                        generation_record=test_record,
                        module_code=module.module_code,
                        operation_code=operation.operation_code,
                        content_digest=test_digest,
                    )
                )

        execution_record = self.executor.run(
            asset_workspace.tests_dir,
            output_root=asset_workspace.workspace_root,
            target_id="generated-suite",
        )
        generation_execution_status = "passed" if execution_record.result_status == "passed" else "failed"
        for record in generation_records:
            record.execution_status = generation_execution_status
            record_path = asset_workspace.records_dir / f"{record.generation_id}.json"
            record_path.write_text(self.renderer.render_generation_record(record), encoding="utf-8")
        execution_record_path = asset_workspace.records_dir / "execution_record.json"
        execution_record_path.write_text(
            json.dumps(execution_record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        asset_manifest, asset_manifest_path = asset_workspace.write_manifest(
            source_document=parsed.source_document,
            assets=generated_assets,
            generation_records=generation_records,
            execution_record=execution_record,
        )

        return PipelineResult(
            source_document=parsed.source_document,
            modules=parsed.modules,
            operations=parsed.operations,
            assertions=parsed.assertions,
            generation_records=generation_records,
            execution_record=execution_record,
            asset_manifest=asset_manifest,
            asset_manifest_path=str(asset_manifest_path),
            generated_paths=generated_paths,
        )

    def _write_generation_record(
        self,
        records_dir: Path,
        source_id: str,
        asset_type: str,
        asset_path: Path,
        template_reference: str,
        module_code: str | None = None,
        operation_code: str | None = None,
        target_asset_digest: str | None = None,
    ) -> GenerationRecord:
        """为生成出的 API 或测试文件写出生成记录。"""
        record = GenerationRecord(
            generation_id=f"gen-{uuid4().hex[:8]}",
            generation_type="api_method" if asset_type == "api_module" else "test_case",
            source_ids=[source_id],
            target_asset_type=asset_type,
            target_asset_path=str(asset_path),
            generator_type="hybrid",
            generated_at=datetime.now(UTC),
            generated_by="codex",
            generation_version="v1",
            template_reference=template_reference,
            module_code=module_code,
            operation_code=operation_code,
            target_asset_digest=target_asset_digest,
            review_status="pending",
            execution_status="not_run",
        )
        violations = self.validator.validate_generation_record(record)
        if violations:
            raise ValueError("; ".join(violations))
        record_path = records_dir / f"{record.generation_id}.json"
        record_path.write_text(self.renderer.render_generation_record(record), encoding="utf-8")
        return record
