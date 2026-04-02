"""`platform_core` 命令行入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from platform_core.services import PlatformApplicationService


def build_parser() -> argparse.ArgumentParser:
    """构建平台核心 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(description="platform_core CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="执行文档驱动最小闭环")
    run_parser.add_argument("--source", required=True, help="OpenAPI/Swagger 文档路径")
    run_parser.add_argument("--output", required=True, help="输出工作目录")

    inspect_parser = subparsers.add_parser("inspect", help="检查已生成工作区的资产清单")
    inspect_parser.add_argument("--workspace", required=True, help="已生成工作区路径")
    return parser


def main() -> int:
    """解析命令并分发到对应的应用服务入口。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        service = PlatformApplicationService(project_root=Path.cwd())
        summary = service.run_document_pipeline_summary(source_path=args.source, output_root=args.output)
        print(json.dumps(summary.model_dump(mode="json"), ensure_ascii=False))
        return 0 if summary.execution_status == "passed" else 1

    if args.command == "inspect":
        service = PlatformApplicationService(project_root=Path.cwd())
        inspection = service.inspect_workspace(output_root=args.workspace)
        print(json.dumps(inspection.model_dump(mode="json"), ensure_ascii=False))
        return 0 if inspection.validation_status == "valid" else 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
