from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

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
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.parser = parser or OpenAPIDocumentParser()
        self.renderer = renderer or TemplateRenderer()
        self.validator = validator or RuleValidator()
        self.executor = executor or PytestExecutor(project_root=self.project_root)

    def run(self, source_path: str | Path, output_root: str | Path) -> PipelineResult:
        parsed = self.parser.parse(source_path)
        workspace = Path(output_root)
        generated_root = workspace / "generated"
        apis_dir = generated_root / "apis"
        tests_dir = generated_root / "tests"
        records_dir = generated_root / "records"
        generated_paths: dict[str, str] = {}
        generation_records: list[GenerationRecord] = []

        for directory in (generated_root, apis_dir, tests_dir, records_dir, generated_root / "reports"):
            directory.mkdir(parents=True, exist_ok=True)
        for init_file in (generated_root / "__init__.py", apis_dir / "__init__.py", tests_dir / "__init__.py"):
            init_file.write_text("", encoding="utf-8")

        modules_by_id = {module.module_id: module for module in parsed.modules}
        operations_by_module: dict[str, list] = {}
        for operation in parsed.operations:
            operations_by_module.setdefault(operation.module_id, []).append(operation)

        for module_id, operations in operations_by_module.items():
            module = modules_by_id[module_id]
            api_path = apis_dir / f"{module.module_code}_api.py"
            api_path.write_text(self.renderer.render_api_module(module, operations), encoding="utf-8")
            generated_paths[f"api::{module.module_code}"] = str(api_path)
            generation_records.append(
                self._write_generation_record(
                    records_dir=records_dir,
                    source_id=parsed.source_document.source_id,
                    asset_type="api_module",
                    asset_path=api_path,
                    template_reference="templates/api/api_module.py.j2",
                )
            )

            for operation in operations:
                violations = self.validator.validate_operation(operation)
                test_path = tests_dir / f"test_{operation.operation_code}.py"
                violations.extend(self.validator.validate_test_file_name(test_path.name))
                if violations:
                    raise ValueError("; ".join(violations))

                assertions = [
                    assertion for assertion in parsed.assertions if assertion.operation_id == operation.operation_id
                ]
                test_path.write_text(
                    self.renderer.render_test_module(module, operation, assertions),
                    encoding="utf-8",
                )
                generated_paths[f"test::{operation.operation_code}"] = str(test_path)
                generation_records.append(
                    self._write_generation_record(
                        records_dir=records_dir,
                        source_id=parsed.source_document.source_id,
                        asset_type="test_case",
                        asset_path=test_path,
                        template_reference="templates/tests/test_module.py.j2",
                    )
                )

        execution_record = self.executor.run(tests_dir, output_root=workspace, target_id="generated-suite")
        execution_record_path = records_dir / "execution_record.json"
        execution_record_path.write_text(
            json.dumps(execution_record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return PipelineResult(
            source_document=parsed.source_document,
            modules=parsed.modules,
            operations=parsed.operations,
            assertions=parsed.assertions,
            generation_records=generation_records,
            execution_record=execution_record,
            generated_paths=generated_paths,
        )

    def _write_generation_record(
        self,
        records_dir: Path,
        source_id: str,
        asset_type: str,
        asset_path: Path,
        template_reference: str,
    ) -> GenerationRecord:
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
            review_status="pending",
            execution_status="not_run",
        )
        record_path = records_dir / f"{record.generation_id}.json"
        record_path.write_text(self.renderer.render_generation_record(record), encoding="utf-8")
        return record
