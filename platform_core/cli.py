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

    subparsers.add_parser("inspect-legacy-public-api", help="检查旧 PublicAPI 目录并输出结构化资产摘要")
    snapshot_legacy_parser = subparsers.add_parser(
        "snapshot-legacy-public-api",
        help="导出旧 PublicAPI 结构化快照到工作区",
    )
    snapshot_legacy_parser.add_argument("--output", required=True, help="输出工作目录")
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
        print(json.dumps(inspection.model_dump(mode="json"), ensure_ascii=False))
        return 0 if inspection.validation_status == "valid" else 1

    if args.command == "inspect-legacy-public-api":
        service = PlatformApplicationService(project_root=Path.cwd())
        inventory = service.inspect_legacy_public_api_catalog()
        print(json.dumps(inventory.model_dump(mode="json"), ensure_ascii=False))
        return 0 if inventory.validation_status == "valid" else 1

    if args.command == "snapshot-legacy-public-api":
        service = PlatformApplicationService(project_root=Path.cwd())
        result = service.snapshot_legacy_public_api_catalog(output_root=args.output)
        print(
            json.dumps(
                {
                    "source_type": result.source_document.source_type,
                    "module_count": len(result.modules),
                    "operation_count": len(result.operations),
                    "execution_status": result.execution_record.result_status,
                    "asset_manifest_path": result.asset_manifest_path,
                },
                ensure_ascii=False,
            )
        )
        return 0 if result.execution_record.result_status == "passed" else 1

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
