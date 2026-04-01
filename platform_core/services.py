"""平台应用服务层。"""

from __future__ import annotations

from pathlib import Path

from platform_core.assets import AssetWorkspace
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

    def run_document_pipeline(self, source_path: str | Path, output_root: str | Path):
        """执行文档驱动最小闭环。"""
        return self.document_pipeline.run(source_path=source_path, output_root=output_root)

    def inspect_workspace(self, output_root: str | Path):
        """检查指定工作区的资产清单和生成结果。"""
        workspace = AssetWorkspace(output_root)
        return workspace.inspect_manifest(validator=self.validator)

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
