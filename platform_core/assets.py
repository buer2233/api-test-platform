from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from platform_core.models import (
    AssetInspectionResult,
    AssetManifest,
    AssetRecord,
    ExecutionRecord,
    GenerationRecord,
    SourceDocument,
)

if TYPE_CHECKING:
    from platform_core.rules import RuleValidator


class AssetWorkspace:
    """V1 资产工作区，统一管理目录、资产清单和清单落盘。"""

    def __init__(self, output_root: str | Path) -> None:
        self.workspace_root = Path(output_root)
        self.generated_root = self.workspace_root / "generated"
        self.apis_dir = self.generated_root / "apis"
        self.tests_dir = self.generated_root / "tests"
        self.records_dir = self.generated_root / "records"
        self.reports_dir = self.generated_root / "reports"

    def prepare(self) -> None:
        for directory in (
            self.generated_root,
            self.apis_dir,
            self.tests_dir,
            self.records_dir,
            self.reports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        for init_file in (
            self.generated_root / "__init__.py",
            self.apis_dir / "__init__.py",
            self.tests_dir / "__init__.py",
        ):
            init_file.write_text("", encoding="utf-8")

    def build_asset_record(
        self,
        asset_type: str,
        asset_path: Path,
        generation_record: GenerationRecord,
        module_code: str | None = None,
        operation_code: str | None = None,
    ) -> AssetRecord:
        return AssetRecord(
            asset_id=f"asset-{uuid4().hex[:8]}",
            asset_type=asset_type,
            asset_path=str(asset_path),
            generation_id=generation_record.generation_id,
            module_code=module_code,
            operation_code=operation_code,
            source_ids=generation_record.source_ids,
            content_digest=self._digest_bytes(asset_path.read_bytes()),
            review_status=generation_record.review_status,
        )

    def write_manifest(
        self,
        source_document: SourceDocument,
        assets: list[AssetRecord],
        generation_records: list[GenerationRecord],
        execution_record: ExecutionRecord,
    ) -> tuple[AssetManifest, Path]:
        manifest = AssetManifest(
            manifest_id=f"manifest-{uuid4().hex[:8]}",
            source_id=source_document.source_id,
            source_type=source_document.source_type,
            source_digest=self._build_source_digest(source_document),
            generated_at=datetime.now(UTC),
            workspace_root=str(self.workspace_root),
            assets=assets,
            generation_ids=[record.generation_id for record in generation_records],
            execution_id=execution_record.execution_id,
            report_path=execution_record.report_path,
        )
        manifest_path = self.records_dir / "asset_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return manifest, manifest_path

    def load_manifest(self) -> AssetManifest:
        manifest_path = self.records_dir / "asset_manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"未找到资产清单: {manifest_path}")
        return AssetManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    def inspect_manifest(self, validator: RuleValidator | None = None) -> AssetInspectionResult:
        manifest_path = self.records_dir / "asset_manifest.json"
        manifest = self.load_manifest()
        validation_errors = validator.validate_asset_manifest(manifest) if validator else []
        missing_assets: list[str] = []
        digest_mismatches: list[str] = []

        for asset in manifest.assets:
            resolved_path = self._resolve_path(asset.asset_path)
            if not resolved_path.exists():
                missing_assets.append(str(resolved_path))
                continue
            if self._digest_bytes(resolved_path.read_bytes()) != asset.content_digest:
                digest_mismatches.append(str(resolved_path))

        report_path = self._resolve_path(manifest.report_path)
        report_exists = bool(report_path and report_path.exists())
        validation_status = "valid"
        if validation_errors or missing_assets or digest_mismatches or (manifest.report_path and not report_exists):
            validation_status = "invalid"

        return AssetInspectionResult(
            manifest_path=str(manifest_path),
            workspace_root=manifest.workspace_root,
            source_id=manifest.source_id,
            asset_count=len(manifest.assets),
            generation_count=len(manifest.generation_ids),
            execution_id=manifest.execution_id,
            report_path=manifest.report_path,
            report_exists=report_exists,
            missing_assets=missing_assets,
            digest_mismatches=digest_mismatches,
            validation_errors=validation_errors,
            validation_status=validation_status,
        )

    @staticmethod
    def _digest_bytes(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _build_source_digest(self, source_document: SourceDocument) -> str:
        candidate_path = source_document.source_path or source_document.raw_reference
        if candidate_path:
            source_path = Path(candidate_path)
            if source_path.exists():
                return self._digest_bytes(source_path.read_bytes())
        fallback = f"{source_document.source_id}:{source_document.source_name}".encode("utf-8")
        return self._digest_bytes(fallback)

    def _resolve_path(self, candidate_path: str | None) -> Path | None:
        if not candidate_path:
            return None
        path = Path(candidate_path)
        if path.is_absolute():
            return path
        return self.workspace_root / candidate_path
