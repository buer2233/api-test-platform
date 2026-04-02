"""平台应用服务层。"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from platform_core.assets import AssetWorkspace
from platform_core.models import (
    DocumentPipelineRunSummary,
    RouteCapabilitySummary,
    ServiceCapabilitySnapshot,
    WorkspaceAssetInventorySummary,
    WorkspaceInspectionSummary,
)
from platform_core.pipeline import DocumentDrivenPipeline
from platform_core.rules import RuleValidator


class PlatformApplicationService:
    """V1 应用服务层，明确当前只支持文档驱动闭环。"""

    def __init__(
        self,
        project_root: str | Path | None = None,
        document_pipeline: DocumentDrivenPipeline | None = None,
        validator: RuleValidator | None = None,
    ) -> None:
        """装配平台当前阶段可用的流水线与治理能力。"""
        self.project_root = Path(project_root or Path(__file__).resolve().parent.parent)
        self.document_pipeline = document_pipeline or DocumentDrivenPipeline(project_root=self.project_root)
        self.validator = validator or RuleValidator()

    @staticmethod
    def supported_routes() -> dict[str, bool]:
        """返回当前 V1 允许和禁止的输入路线。"""
        return {
            "document": True,
            "functional_case": False,
            "traffic_capture": False,
        }

    def describe_capabilities(self) -> ServiceCapabilitySnapshot:
        """返回当前阶段可直接暴露给外部入口的能力快照。"""
        return ServiceCapabilitySnapshot(
            service_stage="v1",
            local_mode_only=True,
            available_commands=["run", "inspect"],
            routes=[
                RouteCapabilitySummary(
                    route_code="document",
                    enabled=True,
                    stage="v1_active",
                    detail="V1 当前开放文档驱动最小闭环，可执行解析、生成、校验与 pytest 回归。",
                ),
                RouteCapabilitySummary(
                    route_code="functional_case",
                    enabled=False,
                    stage="v1_blocked",
                    detail="V1 仅支持文档驱动最小闭环，功能测试用例驱动留待后续阶段开放。",
                ),
                RouteCapabilitySummary(
                    route_code="traffic_capture",
                    enabled=False,
                    stage="v1_blocked",
                    detail="V1 仅支持文档驱动最小闭环，抓包驱动留待后续阶段开放。",
                ),
            ],
        )

    def run_document_pipeline(self, source_path: str | Path, output_root: str | Path):
        """执行文档驱动最小闭环。"""
        return self.document_pipeline.run(source_path=source_path, output_root=output_root)

    @staticmethod
    def build_document_pipeline_summary(result) -> DocumentPipelineRunSummary:
        """把流水线结果转换为对外稳定的运行摘要。"""
        return DocumentPipelineRunSummary(
            route_code="document",
            service_stage="v1",
            source=result.source_document.source_name,
            source_id=result.source_document.source_id,
            source_type=result.source_document.source_type,
            workspace_root=result.asset_manifest.workspace_root,
            modules=len(result.modules),
            operations=len(result.operations),
            generation_count=len(result.generation_records),
            asset_count=len(result.asset_manifest.assets),
            asset_type_breakdown=PlatformApplicationService._build_breakdown(
                asset.asset_type for asset in result.asset_manifest.assets
            ),
            execution_id=result.execution_record.execution_id,
            execution_target=result.execution_record.target_id,
            execution_status=result.execution_record.result_status,
            execution_exit_code=result.execution_record.exit_code,
            total_count=result.execution_record.total_count,
            passed_count=result.execution_record.passed_count,
            failed_count=result.execution_record.failed_count,
            error_count=result.execution_record.error_count,
            skipped_count=result.execution_record.skipped_count,
            report_path=result.execution_record.report_path,
            asset_manifest_path=result.asset_manifest_path,
        )

    def run_document_pipeline_summary(self, source_path: str | Path, output_root: str | Path) -> DocumentPipelineRunSummary:
        """执行文档驱动最小闭环并返回稳定摘要。"""
        result = self.run_document_pipeline(source_path=source_path, output_root=output_root)
        return self.build_document_pipeline_summary(result)

    def inspect_workspace(self, output_root: str | Path):
        """检查指定工作区的资产清单和生成结果。"""
        workspace = AssetWorkspace(output_root)
        return workspace.inspect_manifest(validator=self.validator)

    @staticmethod
    def build_workspace_inspection_summary(result) -> WorkspaceInspectionSummary:
        """把工作区检查结果转换为对外稳定的检查摘要。"""
        return WorkspaceInspectionSummary(
            command_code="inspect",
            service_stage="v1",
            workspace_root=result.workspace_root,
            manifest_path=result.manifest_path,
            source_id=result.source_id,
            source_type=result.source_type,
            validation_status=result.validation_status,
            asset_count=result.asset_count,
            generation_count=result.generation_count,
            execution_id=result.execution_id,
            report_path=result.report_path,
            report_exists=result.report_exists,
            missing_asset_count=len(result.missing_assets),
            missing_generation_record_count=len(result.missing_generation_records),
            digest_mismatch_count=len(result.digest_mismatches),
            validation_error_count=len(result.validation_errors),
            inventory_summary=WorkspaceAssetInventorySummary(
                asset_type_breakdown=PlatformApplicationService._build_breakdown(
                    asset.asset_type for asset in result.assets
                ),
                generation_type_breakdown=PlatformApplicationService._build_breakdown(
                    record.generation_type for record in result.generation_records
                ),
                generation_review_status_breakdown=PlatformApplicationService._build_breakdown(
                    record.review_status for record in result.generation_records
                ),
                generation_execution_status_breakdown=PlatformApplicationService._build_breakdown(
                    record.execution_status for record in result.generation_records
                ),
            ),
            assets=result.assets,
            generation_records=result.generation_records,
            missing_assets=result.missing_assets,
            missing_generation_records=result.missing_generation_records,
            digest_mismatches=result.digest_mismatches,
            validation_errors=result.validation_errors,
        )

    def inspect_workspace_summary(self, output_root: str | Path) -> WorkspaceInspectionSummary:
        """检查指定工作区并返回服务层稳定摘要。"""
        result = self.inspect_workspace(output_root=output_root)
        return self.build_workspace_inspection_summary(result)

    @staticmethod
    def run_functional_case_pipeline(source_path: str | Path, output_root: str | Path):
        """显式阻断 V1 尚未支持的功能用例驱动路线。"""
        raise NotImplementedError(
            f"V1 仅支持文档驱动最小闭环，暂不支持功能测试用例驱动: {source_path} -> {output_root}"
        )

    @staticmethod
    def run_traffic_capture_pipeline(source_path: str | Path, output_root: str | Path):
        """显式阻断 V1 尚未支持的抓包驱动路线。"""
        raise NotImplementedError(
            f"V1 仅支持文档驱动最小闭环，暂不支持抓包驱动: {source_path} -> {output_root}"
        )

    @staticmethod
    def _build_breakdown(values) -> dict[str, int]:
        """把枚举值序列聚合为便于前端和服务接口直接消费的数量分布。"""
        return dict(Counter(value for value in values if value))
