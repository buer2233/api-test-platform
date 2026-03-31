from __future__ import annotations

import argparse
import json
from pathlib import Path

from platform_core.services import PlatformApplicationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="platform_core CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="执行文档驱动最小闭环")
    run_parser.add_argument("--source", required=True, help="OpenAPI/Swagger 文档路径")
    run_parser.add_argument("--output", required=True, help="输出工作目录")

    inspect_parser = subparsers.add_parser("inspect", help="检查已生成工作区的资产清单")
    inspect_parser.add_argument("--workspace", required=True, help="已生成工作区路径")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        service = PlatformApplicationService(project_root=Path.cwd())
        result = service.run_document_pipeline(source_path=args.source, output_root=args.output)
        print(
            json.dumps(
                {
                    "source": result.source_document.source_name,
                    "modules": len(result.modules),
                    "operations": len(result.operations),
                    "execution_target": result.execution_record.target_id,
                    "execution_status": result.execution_record.result_status,
                    "report_path": result.execution_record.report_path,
                    "asset_manifest_path": result.asset_manifest_path,
                },
                ensure_ascii=False,
            )
        )
        return 0 if result.execution_record.result_status == "passed" else 1

    if args.command == "inspect":
        service = PlatformApplicationService(project_root=Path.cwd())
        inspection = service.inspect_workspace(output_root=args.workspace)
        print(
            json.dumps(
                {
                    "manifest_path": inspection.manifest_path,
                    "source_id": inspection.source_id,
                    "asset_count": inspection.asset_count,
                    "generation_count": inspection.generation_count,
                    "validation_status": inspection.validation_status,
                    "report_exists": inspection.report_exists,
                    "missing_assets": inspection.missing_assets,
                    "digest_mismatches": inspection.digest_mismatches,
                    "validation_errors": inspection.validation_errors,
                },
                ensure_ascii=False,
            )
        )
        return 0 if inspection.validation_status == "valid" else 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
