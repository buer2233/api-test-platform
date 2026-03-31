from __future__ import annotations

from pathlib import Path

from platform_core.assets import AssetWorkspace
from platform_core.legacy_assets import LegacyPublicApiCatalogAdapter
from platform_core.pipeline import DocumentDrivenPipeline
from platform_core.rules import RuleValidator


class PlatformApplicationService:
    """V1 应用服务层，明确当前只支持文档驱动闭环。"""

    def __init__(
        self,
        project_root: str | Path | None = None,
        document_pipeline: DocumentDrivenPipeline | None = None,
        legacy_catalog_adapter: LegacyPublicApiCatalogAdapter | None = None,
        validator: RuleValidator | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.document_pipeline = document_pipeline or DocumentDrivenPipeline(project_root=self.project_root)
        self.legacy_catalog_adapter = legacy_catalog_adapter or LegacyPublicApiCatalogAdapter()
        self.validator = validator or RuleValidator()

    @staticmethod
    def supported_routes() -> dict[str, bool]:
        return {
            "document": True,
            "functional_case": False,
            "traffic_capture": False,
        }

    def run_document_pipeline(self, source_path: str | Path, output_root: str | Path):
        return self.document_pipeline.run(source_path=source_path, output_root=output_root)

    def inspect_workspace(self, output_root: str | Path):
        workspace = AssetWorkspace(output_root)
        return workspace.inspect_manifest(validator=self.validator)

    def inspect_legacy_public_api_catalog(self):
        return self.legacy_catalog_adapter.inspect(validator=self.validator)

    def snapshot_legacy_public_api_catalog(self, output_root: str | Path):
        return self.legacy_catalog_adapter.export(output_root=output_root, validator=self.validator)

    @staticmethod
    def run_functional_case_pipeline(source_path: str | Path, output_root: str | Path):
        raise NotImplementedError(
            f"V1 仅支持文档驱动最小闭环，暂不支持功能测试用例驱动: {source_path} -> {output_root}"
        )

    @staticmethod
    def run_traffic_capture_pipeline(source_path: str | Path, output_root: str | Path):
        raise NotImplementedError(
            f"V1 仅支持文档驱动最小闭环，暂不支持抓包驱动: {source_path} -> {output_root}"
        )
