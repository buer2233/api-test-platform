from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from uuid import uuid4

from platform_core.assets import AssetWorkspace
from platform_core.models import (
    ApiModule,
    ApiOperation,
    AssertionCandidate,
    ExecutionRecord,
    GenerationRecord,
    LegacyApiInventoryResult,
    PipelineResult,
    SourceDocument,
)
from platform_core.rules import RuleValidator


class LegacyPublicApiCatalogAdapter:
    """把旧 PublicAPI 操作目录转换为 platform_core 可消费的结构化快照。"""

    def __init__(self, imported_by: str = "platform_core") -> None:
        self.imported_by = imported_by

    @staticmethod
    def _load_catalog():
        module = import_module("api_test.legacy_api_catalog")
        return module.PUBLIC_API_OPERATION_CATALOG

    def inspect(self) -> LegacyApiInventoryResult:
        source_id = "src-existing-public-api"
        source_document = SourceDocument(
            source_id=source_id,
            source_type="existing_api_asset",
            source_name="api_test_public_api",
            source_path="api_test/core/public_api.py",
            source_version="v1-legacy-catalog",
            source_summary="由旧 PublicAPI 目录治理转换的既有接口资产快照",
            imported_at=datetime.now(UTC),
            imported_by=self.imported_by,
            raw_reference="api_test.legacy_api_catalog:PUBLIC_API_OPERATION_CATALOG",
        )

        module_map: dict[str, ApiModule] = {}
        operations: list[ApiOperation] = []
        private_env_operation_count = 0

        for legacy_operation in self._load_catalog().values():
            module = module_map.setdefault(
                legacy_operation.module_code,
                ApiModule(
                    module_id=f"mod-legacy-{legacy_operation.module_code}",
                    module_name=legacy_operation.module_code,
                    module_code=legacy_operation.module_code,
                    module_path_hint=f"api_test/core/public_api.py::{legacy_operation.module_code}",
                    module_type="common",
                    module_desc=f"旧 PublicAPI 模块目录：{legacy_operation.module_code}",
                    source_ids=[source_id],
                    tags=["legacy_public_api"],
                ),
            )

            tags = ["legacy_public_api"]
            if legacy_operation.requires_private_env:
                tags.append("private_env")
                private_env_operation_count += 1

            operations.append(
                ApiOperation(
                    operation_id=f"op-legacy-{legacy_operation.operation_code}",
                    module_id=module.module_id,
                    operation_name=legacy_operation.operation_name,
                    operation_code=legacy_operation.operation_code,
                    http_method=legacy_operation.http_method,
                    path=legacy_operation.path_template,
                    summary=legacy_operation.description,
                    description=f"由旧 PublicAPI 目录治理转换的既有接口资产：{legacy_operation.operation_name}",
                    tags=tags,
                    success_codes=[200] if legacy_operation.response_mode == "json" else [],
                    source_ids=[source_id],
                    metadata={
                        "payload_mode": legacy_operation.payload_mode,
                        "response_mode": legacy_operation.response_mode,
                        "requires_private_env": legacy_operation.requires_private_env,
                        "source_layer": "api_test.core.public_api",
                    },
                )
            )

        modules = sorted(module_map.values(), key=lambda item: item.module_code)
        operations.sort(key=lambda item: item.operation_code)

        return LegacyApiInventoryResult(
            source_document=source_document,
            module_count=len(modules),
            operation_count=len(operations),
            private_env_operation_count=private_env_operation_count,
            modules=modules,
            operations=operations,
        )

    def export(
        self,
        output_root: str | Path,
        validator: RuleValidator | None = None,
    ) -> PipelineResult:
        inventory = self.inspect()
        rule_validator = validator or RuleValidator()
        workspace = AssetWorkspace(output_root)
        workspace.prepare()

        generated_paths: dict[str, str] = {}
        generation_records: list[GenerationRecord] = []
        generated_assets = []

        for module in inventory.modules:
            module_operations = [operation for operation in inventory.operations if operation.module_id == module.module_id]
            violations: list[str] = []
            for operation in module_operations:
                violations.extend(rule_validator.validate_operation(operation))
            if violations:
                raise ValueError("; ".join(violations))

            module_path = workspace.apis_dir / f"legacy_{module.module_code}_inventory.json"
            module_path.write_text(
                json.dumps(
                    {
                        "source_document": inventory.source_document.model_dump(mode="json"),
                        "module": module.model_dump(mode="json"),
                        "operations": [operation.model_dump(mode="json") for operation in module_operations],
                        "operation_count": len(module_operations),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            generated_paths[f"api::legacy::{module.module_code}"] = str(module_path)

            generation_record = self._write_generation_record(
                records_dir=workspace.records_dir,
                source_id=inventory.source_document.source_id,
                asset_path=module_path,
            )
            generation_records.append(generation_record)
            generated_assets.append(
                workspace.build_asset_record(
                    asset_type="api_module",
                    asset_path=module_path,
                    generation_record=generation_record,
                    module_code=module.module_code,
                )
            )

        execution_record = self._write_execution_report(
            workspace=workspace,
            inventory=inventory,
            target_id="legacy-public-api-catalog",
        )
        execution_record_path = workspace.records_dir / "execution_record.json"
        execution_record_path.write_text(
            json.dumps(execution_record.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        asset_manifest, asset_manifest_path = workspace.write_manifest(
            source_document=inventory.source_document,
            assets=generated_assets,
            generation_records=generation_records,
            execution_record=execution_record,
        )

        return PipelineResult(
            source_document=inventory.source_document,
            modules=inventory.modules,
            operations=inventory.operations,
            assertions=[],
            generation_records=generation_records,
            execution_record=execution_record,
            asset_manifest=asset_manifest,
            asset_manifest_path=str(asset_manifest_path),
            generated_paths=generated_paths,
        )

    @staticmethod
    def _write_generation_record(records_dir: Path, source_id: str, asset_path: Path) -> GenerationRecord:
        record = GenerationRecord(
            generation_id=f"gen-{uuid4().hex[:8]}",
            generation_type="api_method",
            source_ids=[source_id],
            target_asset_type="api_module",
            target_asset_path=str(asset_path),
            generator_type="rule_based",
            generated_at=datetime.now(UTC),
            generated_by="codex",
            generation_version="v1-legacy-catalog",
            template_reference="legacy_api_catalog_exporter",
            review_status="pending",
            execution_status="passed",
        )
        violations = RuleValidator.validate_generation_record(record)
        if violations:
            raise ValueError("; ".join(violations))
        record_path = records_dir / f"{record.generation_id}.json"
        record_path.write_text(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    @staticmethod
    def _write_execution_report(
        workspace: AssetWorkspace,
        inventory: LegacyApiInventoryResult,
        target_id: str,
    ) -> ExecutionRecord:
        report_path = workspace.reports_dir / "legacy_public_api_inventory.json"
        started_at = datetime.now(UTC)
        report_path.write_text(
            json.dumps(
                {
                    "source_document": inventory.source_document.model_dump(mode="json"),
                    "module_count": inventory.module_count,
                    "operation_count": inventory.operation_count,
                    "private_env_operation_count": inventory.private_env_operation_count,
                    "validation_status": "valid",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        ended_at = datetime.now(UTC)
        return ExecutionRecord(
            execution_id=f"exec-{target_id}",
            target_type="api_module",
            target_id=target_id,
            execution_level="structure_check",
            started_at=started_at,
            ended_at=ended_at,
            result_status="passed",
            report_path=str(report_path),
            error_summary="",
            environment="local",
        )
